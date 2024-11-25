from datetime import datetime, timedelta, timezone
import re
from sqlalchemy.exc import DataError
from typing import Optional

from constants.get_constants import get_constants
from .core import CoreProcess
from managers import DBManager, SFRRecordManager, KMeansManager, SFRElasticRecordManager, ElasticsearchManager, RedisManager
from model import Record, Work
from logger import create_log

logger = create_log(__name__)


class ClusterProcess(CoreProcess):
    MAX_MATCH_DISTANCE = 4
    CLUSTER_BATCH_SIZE = 50
    CLUSTER_SIZE_LIMIT = 10000
    IDENTIFIERS_TO_MATCH = r'\|(?:isbn|issn|oclc|lccn|owi)$'

    def __init__(self, *args):
        super(ClusterProcess, self).__init__(*args[:4])

        self.ingest_limit = int(args[4]) if len(args) >= 5 and args[4] else None

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.redis_manager = RedisManager()
        self.redis_manager.createRedisClient()

        self.elastic_search_manager = ElasticsearchManager()
        
        self.elastic_search_manager.createElasticConnection()
        self.elastic_search_manager.createElasticSearchIngestPipeline()
        self.elastic_search_manager.createElasticSearchIndex()

        self.constants = get_constants()

    def runProcess(self):
        try:
            if self.process == 'daily':
                self.cluster_records()
            elif self.process == 'complete':
                self.cluster_records(full=True)
            elif self.process == 'custom':
                self.cluster_records(start_datetime=self.ingestPeriod)
            elif self.process == 'single':
                self.cluster_records(record_uuid=self.singleRecord)
            else: 
                logger.warning(f'Unknown cluster process type {self.process}')
        except Exception as e:
            logger.exception('Failed to run cluster process')
            raise e
        finally:
            self.db_manager.session.close_connection()

    def cluster_records(self, full=False, start_datetime=None, record_uuid=None):
        get_unclustered_records_query = (
            self.db_manager.session.query(Record)
                .filter(Record.frbr_status == 'complete')
                .filter(Record.cluster_status == False)
                .filter(Record.source != 'oclcClassify')
                .filter(Record.source != 'oclcCatalog')
                .filter(Record.title.isnot(None))
        )

        if not full:
            if not start_datetime:
                start_datetime = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            elif self.process == 'custom':
                start_datetime = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S')

            get_unclustered_records_query = get_unclustered_records_query.filter(Record.date_modified > start_datetime)

        if record_uuid:
            get_unclustered_records_query = get_unclustered_records_query.filter(Record.uuid == record_uuid)

        works_to_index = []
        work_ids_to_delete = set()

        while unclustered_record := get_unclustered_records_query.first():
            try:
                work, stale_work_ids = self.cluster_record(unclustered_record)
                works_to_index.append(work)
                work_ids_to_delete.update(stale_work_ids)
            except ClusterError:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                
                self.update_cluster_status([unclustered_record.id])
                self.db_manager.session.commit()
            except Exception as e:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                raise e

            if len(works_to_index) >= self.CLUSTER_BATCH_SIZE:
                self.update_elastic_search(works_to_index, work_ids_to_delete)
                logger.info(f'Clustered {len(works_to_index)} works')
                works_to_index = []

                self.delete_stale_works(work_ids_to_delete)
                work_ids_to_delete = set()

                self.db_manager.session.commit()

        logger.info(f'Clustered {len(works_to_index)} works')
        self.update_elastic_search(works_to_index, work_ids_to_delete)
        self.delete_stale_works(work_ids_to_delete)

        self.db_manager.session.commit()

    def cluster_record(self, record: Record):
        matched_record_ids = self.find_all_matching_records(record) + [record.id]

        clustered_editions, records = self.cluster_matched_records(matched_record_ids)
        work, stale_work_ids = self.create_work_from_editions(clustered_editions, records)

        try:
            self.db_manager.session.flush()
        except Exception:
            self.db_manager.session.rollback()
            logger.exception(f'Unable to cluster record {record}')

            raise ClusterError(f'Unable to cluster record {record}')

        self.update_cluster_status(matched_record_ids)

        return work, stale_work_ids

    def update_cluster_status(self, record_ids: list[str], cluster_status: bool=True):
        (
            self.db_manager.session.query(Record)
                .filter(Record.id.in_(list(set(record_ids))))
                .update(
                    {
                        'cluster_status': cluster_status, 
                        'frbr_status': 'complete'
                    }
                )
        )

    def update_elastic_search(self, works_to_index: list, word_ids_to_delete: set):
        self.elastic_search_manager.deleteWorkRecords(word_ids_to_delete)
        self.index_works_in_elastic_search(works_to_index)

    def delete_stale_works(self, work_ids: set[str]):
        self.deleteRecordsByQuery(self.db_manager.session.query(Work).filter(Work.id.in_(list(work_ids))))

    def cluster_matched_records(self, record_ids: list[str]):
        records = self.db_manager.session.query(Record).filter(Record.id.in_(record_ids)).all()

        kmean_manager = KMeansManager(records)

        kmean_manager.createDF()
        kmean_manager.generateClusters()
        editions = kmean_manager.parseEditions()

        return editions, records

    def find_all_matching_records(self, record: Record):
        tokenized_record_title = self.tokenize_title(record.title)
        ids_to_match = list(filter(lambda id: re.search(self.IDENTIFIERS_TO_MATCH, id), record.identifiers))

        matched_record_ids = set()
        checked_ids = set()

        ids_to_check = ids_to_match

        for match_distance in range(0, self.MAX_MATCH_DISTANCE):
            matched_records = self.get_matched_records(list(ids_to_check), matched_record_ids.copy())

            if len(matched_records) == 0:
                break

            checked_ids.update(ids_to_check)

            ids_to_check = set()

            for matched_record in matched_records:
                matched_record_title, matched_record_id, matched_record_identifiers = matched_record

                tokenized_matched_record_title = self.tokenize_title(matched_record_title)

                if match_distance > 0 and not self.titles_overlap(tokenized_record_title, tokenized_matched_record_title):
                    continue

                ids_to_check.update(list(
                    filter(
                        lambda id: re.search(self.IDENTIFIERS_TO_MATCH, id) and id not in checked_ids,
                        matched_record_identifiers
                    )
                ))

                matched_record_ids.add(matched_record_id)

        if len(matched_record_ids) > self.CLUSTER_SIZE_LIMIT:
            raise ClusterError(f'Records matched is greater than {self.CLUSTER_SIZE_LIMIT}')

        return list(matched_record_ids)
    
    def get_matched_records(self, identifiers: list[str], already_matched_record_ids: list[str]):
        batch_size = 100
        matched_records = []

        for i in range(0, len(identifiers), batch_size):
            id_batch = self.format_identifiers(identifiers[i:i+batch_size])

            try:
                records = (
                    self.db_manager.session.query(Record.title, Record.id, Record.identifiers)
                        .filter(~Record.id.in_(list(already_matched_record_ids)))
                        .filter(Record.identifiers.overlap(id_batch))
                        .filter(Record.title.isnot(None))
                        .all()
                )

                matched_records.extend(records)
            except DataError:
                logger.exception('Unable to get matching records')

        return matched_records

    def create_work_from_editions(self, editions, records):
        record_manager = SFRRecordManager(self.db_manager.session, self.constants['iso639'])

        work_data = record_manager.buildWork(records, editions)

        record_manager.saveWork(work_data)

        stale_work_ids = record_manager.mergeRecords()

        return record_manager.work, stale_work_ids

    def index_works_in_elastic_search(self, works: Work):
        work_documents = []

        for work in works:
            elastic_manager = SFRElasticRecordManager(work)
            elastic_manager.getCreateWork()
            work_documents.append(elastic_manager.work)

        self.elastic_search_manager.saveWorkRecords(work_documents)

    def titles_overlap(self, tokenized_record_title: set, tokenized_matched_record_title: set):
        if len(tokenized_record_title) == 1 and not tokenized_record_title <= tokenized_matched_record_title:
            return False
        elif len(tokenized_matched_record_title) == 1 and not tokenized_record_title >= tokenized_matched_record_title:
            return False
        elif (len(tokenized_record_title) > 1 and len(tokenized_matched_record_title) > 1) and len(tokenized_record_title & tokenized_matched_record_title) < 2:
            return False

        return True

    def tokenize_title(self, title: Optional[str]):
        if not title: 
            raise ClusterError(f'Invalid title {title}')

        title_tokens = re.findall(r'(\w+)', title.lower())

        return set(title_tokens) - set(['a', 'an', 'the', 'of'])

    def format_identifiers(self, identifiers):
        formatted_ids = []

        for id in identifiers:
            formatted_id = f'"{id}"' if re.search(r'[{},]{1}', id) else id
            formatted_ids.append(formatted_id)

        return '{{{}}}'.format(','.join(formatted_ids))


class ClusterError(Exception): pass
