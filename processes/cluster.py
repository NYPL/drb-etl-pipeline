from datetime import datetime, timedelta, timezone
from math import ceil
import re
from sqlalchemy.exc import DataError

from .core import CoreProcess
from managers import SFRRecordManager, KMeansManager, SFRElasticRecordManager
from model import Record, Work, Edition
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
        works_to_delete = set()

        while unclustered_record := get_unclustered_records_query.first():
            try:
                work, work_ids_to_delete = self.cluster_record(unclustered_record)
                works_to_index.append(work)
                works_to_delete.update(work_ids_to_delete)
            except ClusterError:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                
                self.update_cluster_status([unclustered_record.id])
                self.session.commit()
            except Exception as e:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                raise e

            if len(works_to_index) >= self.CLUSTER_BATCH_SIZE:
                self.update_elastic_search(works_to_index, works_to_delete)
                works_to_index = []

                self.delete_stale_works(works_to_delete)
                works_to_delete = set()

                self.session.commit()

        self.update_elastic_search(works_to_index, works_to_delete)
        self.delete_stale_works(works_to_delete)

        self.session.commit()

    def cluster_record(self, record: Record):
        logger.info('Clustering {}'.format(record))

        self.matchTitleTokens = self.tokenize_title(record.title)

        record_ids = self.find_all_matching_records(record.identifiers)

        record_ids.append(record.id)

        clustered_editions, records = self.cluster_matched_records(record_ids)
        work, deletedUUIDs = self.create_work_from_editions(clustered_editions, records)

        try:
            self.session.flush()
        except Exception:
            self.session.rollback()
            logger.exception(f'Unable to cluster record {record}')

            raise ClusterError('Malformed DCDW Record Received')

        self.update_cluster_status(record_ids)

        return work, deletedUUIDs

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

    def delete_stale_works(self, deletingWorks):
        editionIDTuples = self.session.query(Edition.id).join(Work).filter(Work.uuid.in_(list(deletingWorks))).all()
        editionIDs = [ed[0] for ed in editionIDTuples]
        self.deleteRecordsByQuery(self.session.query(Edition).filter(Edition.id.in_(editionIDs)))
        self.deleteRecordsByQuery(self.session.query(Work).filter(Work.uuid.in_(list(deletingWorks))))

    def cluster_matched_records(self, record_ids: list[str]):
        records = self.session.query(Record).filter(Record.id.in_(record_ids)).all()

        kmean_manager = KMeansManager(records)

        kmean_manager.createDF()
        kmean_manager.generateClusters()
        editions = kmean_manager.parseEditions()

        return editions, records

    def find_all_matching_records(self, identifiers):
        idens = list(filter(lambda x: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', x) != None, identifiers))

        return self.query_identifiers(idens)

    def create_work_from_editions(self, editions, instances):
        record_manager = SFRRecordManager(self.session, self.statics['iso639'])

        work_data = record_manager.buildWork(instances, editions)

        record_manager.saveWork(work_data)

        record_ids_to_delete = record_manager.mergeRecords()

        return record_manager.work, record_ids_to_delete

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

    def get_record_batches(self, identifiers, matchedIDs):
        step = 100
        i = 0
        totalMatches = []

        while i < len(identifiers):
            idArray = self.format_identifiers(identifiers[i:i+step])

            try:
                matches = self.session.query(Record.title, Record.id, Record.identifiers)\
                    .filter(~Record.id.in_(list(matchedIDs)))\
                    .filter(Record.identifiers.overlap(idArray))\
                    .all()

                totalMatches.extend(matches)
            except DataError as e:
                logger.warning('Unable to execute batch id query')

            i += step

        return totalMatches

    def index_works_in_elastic_search(self, dbWorks):
        esWorks = []

        for dbWork in dbWorks:
            elasticManager = SFRElasticRecordManager(dbWork)
            elasticManager.getCreateWork()
            esWorks.append(elasticManager.work)

        self.saveWorkRecords(esWorks)

    def compare_title_tokens(self, recTitle):
        recTitleTokens = self.tokenize_title(recTitle)

        if len(self.matchTitleTokens) == 1 and (self.matchTitleTokens <= recTitleTokens) is not True:
            return True
        elif len(recTitleTokens) == 1 and (self.matchTitleTokens >= recTitleTokens) is not True:
            return True
        elif (len(self.matchTitleTokens) > 1 and len(recTitleTokens) > 1) and len(self.matchTitleTokens & recTitleTokens) < 2:
            return True

        return False

    @staticmethod
    def tokenize_title(title: str):
        try:
            lowerTitle = title.lower()
        except AttributeError:
            logger.error('Unable to parse record title')
            raise ClusterError('Invalid title received')

        titleTokens = re.findall(r'(\w+)', lowerTitle)

        titleTokenSet = set(titleTokens) - set(['a', 'an', 'the', 'of'])

        return titleTokenSet

    @staticmethod
    def format_identifiers(identifiers):
        idenStrings = []

        for iden in identifiers:
            idenStr = '"{}"'.format(iden) if re.search(r'[{},]{1}', iden) else iden
            idenStrings.append(idenStr)

        return '{{{}}}'.format(','.join(idenStrings))


class ClusterError(Exception): pass
