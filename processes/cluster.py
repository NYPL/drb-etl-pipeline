from datetime import datetime, timedelta, timezone
import re
from sqlalchemy.exc import DataError
from typing import Optional

from .core import CoreProcess
from managers import SFRRecordManager, KMeansManager, SFRElasticRecordManager
from model import Record, Work
from logger import createLog


logger = createLog(__name__)


class ClusterProcess(CoreProcess):
    CLUSTER_BATCH_SIZE = 50
    CLUSTER_SIZE_LIMIT = 10000

    def __init__(self, *args):
        super(ClusterProcess, self).__init__(*args[:4])

        self.ingest_limit = int(args[4]) if len(args) >= 5 and args[4] else None

        self.generateEngine()
        self.createSession()

        self.createRedisClient()
        
        self.createElasticConnection()
        self.createElasticSearchIngestPipeline()
        self.createElasticSearchIndex()

    def runProcess(self):
        try:
            if self.process == 'daily':
                self.cluster_records()
            elif self.process == 'complete':
                self.cluster_records(full=True)
            elif self.process == 'custom':
                self.cluster_records(start_datetime=self.ingestPeriod)
            else: 
                logger.warning(f'Unknown cluster process type {self.process}')
        except Exception as e:
            logger.exception('Failed to run cluster process')
            raise e
        finally:
            self.closeConnection()

    def cluster_records(self, full=False, start_datetime=None):
        get_unclustered_records_query = (
            self.session.query(Record)
                .filter(Record.frbr_status == 'complete')
                .filter(Record.cluster_status == False)
                .filter(Record.source != 'oclcClassify')
                .filter(Record.source != 'oclcCatalog')
        )

        if not full:
            if not start_datetime:
                start_datetime = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            elif self.process == 'custom':
                start_datetime = datetime.strptime(start_datetime, '%Y-%m-%dT%H:%M:%S')

            get_unclustered_records_query = get_unclustered_records_query.filter(Record.date_modified > start_datetime)

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
                self.session.commit()
            except Exception as e:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                raise e

            if len(works_to_index) >= self.CLUSTER_BATCH_SIZE:
                self.update_elastic_search(works_to_index, work_ids_to_delete)
                works_to_index = []

                self.delete_stale_works(work_ids_to_delete)
                work_ids_to_delete = set()

                self.session.commit()

        self.update_elastic_search(works_to_index, work_ids_to_delete)
        self.delete_stale_works(work_ids_to_delete)

        self.session.commit()

    def cluster_record(self, record: Record):
        logger.info('Clustering {}'.format(record))

        matched_record_ids = self.find_all_matching_records(record) + [record.id]

        clustered_editions, records = self.cluster_matched_records(matched_record_ids)
        work, stale_work_ids = self.create_work_from_editions(clustered_editions, records)

        try:
            self.session.flush()
        except Exception:
            self.session.rollback()
            logger.exception(f'Unable to cluster record {record}')

            raise ClusterError('Malformed DCDW Record Received')

        self.update_cluster_status(matched_record_ids)

        return work, stale_work_ids

    def update_cluster_status(self, record_ids: list[str], cluster_status: bool=True):
        (
            self.session.query(Record)
                .filter(Record.id.in_(list(set(record_ids))))
                .update(
                    {
                        'cluster_status': cluster_status, 
                        'frbr_status': 'complete'
                    }
                )
        )

    def update_elastic_search(self, indexingWorks, deletingWorks):
        self.deleteWorkRecords(deletingWorks)
        self.index_works_in_elastic_search(indexingWorks)

    def delete_stale_works(self, work_ids: set[str]):
        self.deleteRecordsByQuery(self.session.query(Work).filter(Work.uuid.in_(list(work_ids))))

    def cluster_matched_records(self, record_ids: list[str]):
        records = self.session.query(Record).filter(Record.id.in_(record_ids)).all()

        kmean_manager = KMeansManager(records)

        kmean_manager.createDF()
        kmean_manager.generateClusters()
        editions = kmean_manager.parseEditions()

        return editions, records

    def find_all_matching_records(self, record: Record):
        ids = list(filter(lambda id: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', id) != None, record.identifiers))

        return self.query_identifiers(ids)

    def create_work_from_editions(self, editions, instances):
        record_manager = SFRRecordManager(self.session, self.statics['iso639'])

        work_data = record_manager.buildWork(instances, editions)

        record_manager.saveWork(work_data)

        stale_work_ids = record_manager.mergeRecords()

        return record_manager.work, stale_work_ids

    def query_identifiers(self, ids: list[str]):
        matched_ids = set()
        checked_ids = set()

        ids_to_check = ids

        for iteration in range(0, 4):
            record_batches = self.get_record_batches(list(ids_to_check), matched_ids.copy())

            if len(record_batches) == 0:
                break

            checked_ids.update(ids_to_check)

            ids_to_check = set()

            for record_batch in record_batches:
                record_title, record_id, record_ids = record_batch

                if iteration > 0 and self.compare_title_tokens(record_title):
                    continue

                ids_to_check.update(list(filter(
                    lambda id: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', id) != None and id not in checked_ids,
                    record_ids)
                ))
                matched_ids.add(record_id)

        if len(matched_ids) > self.CLUSTER_SIZE_LIMIT:
            raise ClusterError(f'Records matched is greater than {self.CLUSTER_SIZE_LIMIT}')

        return list(matched_ids)

    def get_record_batches(self, identifiers, match_ids):
        batch = 100
        total_matches = []

        for i in range(0, len(identifiers), batch):
            id_batch = self.format_identifiers(identifiers[i:i+batch])

            try:
                matches = (
                    self.session.query(Record.title, Record.id, Record.identifiers)
                        .filter(~Record.id.in_(list(match_ids)))
                        .filter(Record.identifiers.overlap(id_batch))
                        .all()
                )

                total_matches.extend(matches)
            except DataError:
                logger.warning('Unable to execute batch id query')

        return total_matches

    def index_works_in_elastic_search(self, dbWorks):
        esWorks = []

        for dbWork in dbWorks:
            elasticManager = SFRElasticRecordManager(dbWork)
            elasticManager.getCreateWork()
            esWorks.append(elasticManager.work)

        self.saveWorkRecords(esWorks)

    def compare_title_tokens(self, record_title: str):
        recTitleTokens = self.tokenize_title(record_title)

        if len(self.matchTitleTokens) == 1 and (self.matchTitleTokens <= recTitleTokens) is not True:
            return True
        elif len(recTitleTokens) == 1 and (self.matchTitleTokens >= recTitleTokens) is not True:
            return True
        elif (len(self.matchTitleTokens) > 1 and len(recTitleTokens) > 1) and len(self.matchTitleTokens & recTitleTokens) < 2:
            return True

        return False

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
