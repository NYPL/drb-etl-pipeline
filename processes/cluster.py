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
                
                self.updateMatchedRecordsStatus([unclustered_record.id])
                self.session.commit()
            except Exception as e:
                logger.exception(f'Failed to cluster record {unclustered_record}')
                raise e

            if len(works_to_index) >= self.CLUSTER_BATCH_SIZE:
                self.updateElasticSearch(works_to_index, works_to_delete)
                works_to_index = []

                self.deleteStaleWorks(works_to_delete)
                works_to_delete = set()

                self.session.commit()

        self.updateElasticSearch(works_to_index, works_to_delete)
        self.deleteStaleWorks(works_to_delete)

        self.session.commit()

    def cluster_record(self, record: Record):
        logger.info('Clustering {}'.format(record))

        self.matchTitleTokens = self.tokenizeTitle(record.title)

        matchedIDs = self.findAllMatchingRecords(record.identifiers)

        matchedIDs.append(record.id)

        clusteredEditions, instances = self.clusterMatchedRecords(matchedIDs)
        dbWork, deletedUUIDs = self.createWorkFromEditions(clusteredEditions, instances)

        try:
            self.session.flush()
        except Exception:
            self.session.rollback()
            logger.exception(f'Unable to cluster record {record}')

            raise ClusterError('Malformed DCDW Record Received')

        self.updateMatchedRecordsStatus(matchedIDs)

        return dbWork, deletedUUIDs

    def updateMatchedRecordsStatus(self, matchedIDs):
        self.session.query(Record)\
            .filter(Record.id.in_(list(set(matchedIDs))))\
            .update({'cluster_status': True, 'frbr_status': 'complete'})

    def updateElasticSearch(self, indexingWorks, deletingWorks):
        self.deleteWorkRecords(deletingWorks)
        self.indexWorksInElasticSearch(indexingWorks)

    def deleteStaleWorks(self, deletingWorks):
        editionIDTuples = self.session.query(Edition.id).join(Work).filter(Work.uuid.in_(list(deletingWorks))).all()
        editionIDs = [ed[0] for ed in editionIDTuples]
        self.deleteRecordsByQuery(self.session.query(Edition).filter(Edition.id.in_(editionIDs)))
        self.deleteRecordsByQuery(self.session.query(Work).filter(Work.uuid.in_(list(deletingWorks))))

    def clusterMatchedRecords(self, recIDs):
        records = self.session.query(Record).filter(Record.id.in_(recIDs)).all()

        mlModel = KMeansManager(records)
        mlModel.createDF()
        mlModel.generateClusters()
        editions = mlModel.parseEditions()

        return editions, records

    def findAllMatchingRecords(self, identifiers):
        idens = list(filter(lambda x: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', x) != None, identifiers))

        return self.queryIdens(idens)

    def createWorkFromEditions(self, editions, instances):
        recordManager = SFRRecordManager(self.session, self.statics['iso639'])

        workData = recordManager.buildWork(instances, editions)

        recordManager.saveWork(workData)

        deletedRecordUUIDs = recordManager.mergeRecords()

        return recordManager.work, deletedRecordUUIDs

    def queryIdens(self, idens):
        matchedIDs = set()
        checkedIdens = set()

        checkIdens = idens

        iterations = 0

        while iterations < 4:
            matches = self.getRecordBatches(list(checkIdens), matchedIDs.copy())

            if len(matches) == 0:
                break

            checkedIdens.update(checkIdens)

            checkIdens = set()
            for match in matches:
                recTitle, recID, recIdentifiers = match

                if iterations > 0 and self.compareTitleTokens(recTitle):
                    continue

                checkIdens.update(list(filter(
                    lambda x: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', x) != None and x not in checkedIdens,
                    recIdentifiers)
                ))
                matchedIDs.add(recID)

            iterations += 1

        if len(matchedIDs) > 10000:
            logger.info(matchedIDs)
            raise ClusterError('Clustering Error encountered, unreasonable number of records matched')

        return list(matchedIDs)

    def getRecordBatches(self, identifiers, matchedIDs):
        step = 100
        i = 0
        totalMatches = []

        while i < len(identifiers):
            idArray = self.formatIdenArray(identifiers[i:i+step])

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

    def indexWorksInElasticSearch(self, dbWorks):
        esWorks = []

        for dbWork in dbWorks:
            elasticManager = SFRElasticRecordManager(dbWork)
            elasticManager.getCreateWork()
            esWorks.append(elasticManager.work)

        # elasticManager.saveWork()
        self.saveWorkRecords(esWorks)

    def compareTitleTokens(self, recTitle):
        recTitleTokens = self.tokenizeTitle(recTitle)

        if len(self.matchTitleTokens) == 1 and (self.matchTitleTokens <= recTitleTokens) is not True:
            return True
        elif len(recTitleTokens) == 1 and (self.matchTitleTokens >= recTitleTokens) is not True:
            return True
        elif (len(self.matchTitleTokens) > 1 and len(recTitleTokens) > 1) and len(self.matchTitleTokens & recTitleTokens) < 2:
            return True

        return False

    @staticmethod
    def tokenizeTitle(title):
        try:
            lowerTitle = title.lower()
        except AttributeError:
            logger.error('Unable to parse record title')
            raise ClusterError('Invalid title received')

        titleTokens = re.findall(r'(\w+)', lowerTitle)

        titleTokenSet = set(titleTokens) - set(['a', 'an', 'the', 'of'])

        return titleTokenSet

    @staticmethod
    def formatIdenArray(identifiers):
        idenStrings = []

        for iden in identifiers:
            idenStr = '"{}"'.format(iden) if re.search(r'[{},]{1}', iden) else iden
            idenStrings.append(idenStr)

        return '{{{}}}'.format(','.join(idenStrings))


class ClusterError(Exception): pass
