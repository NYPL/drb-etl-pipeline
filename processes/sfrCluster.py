from datetime import datetime, timedelta
from math import ceil
import re
from sqlalchemy.exc import DataError
from sqlalchemy.orm.exc import StaleDataError

from .core import CoreProcess
from managers import SFRRecordManager, KMeansManager, SFRElasticRecordManager
from model import Record, Work, Edition
from logger import createLog

logger = createLog(__name__)


class ClusterProcess(CoreProcess):
    def __init__(self, *args):
        super(ClusterProcess, self).__init__(*args[:4])

        self.ingestLimit = int(args[4]) if args[4] else None

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # Redis Connection
        self.createRedisClient()

        # ElasticSearch Connection
        self.createElasticConnection()
        self.createElasticSearchIngestPipeline()
        self.createElasticSearchIndex()

    def runProcess(self):
        if self.process == 'daily':
            self.clusterRecords()
        elif self.process == 'complete':
            self.clusterRecords(full=True)
        elif self.process == 'custom':
            self.clusterRecords(startDateTime=self.ingestPeriod)

    def clusterRecords(self, full=False, startDateTime=None):
        baseQuery = self.session.query(Record)\
            .filter(Record.frbr_status == 'complete')\
            .filter(Record.cluster_status == False)\
            .filter(Record.source != 'oclcClassify')\
            .filter(Record.source != 'oclcCatalog')

        if full is False:
            if not startDateTime:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
            elif self.process == 'custom':
                startDateTime = datetime.strptime(startDateTime, '%Y-%m-%dT%H:%M:%S')

            baseQuery = baseQuery.filter(Record.date_modified > startDateTime)
        
        indexingWorks = []
        deletingWorks = set()
        while True:
            rec = baseQuery.first()

            if rec is None:
                break

            try:
                dbWork, deletedUUIDs = self.clusterRecord(rec)
                indexingWorks.append(dbWork)
                deletingWorks.update(deletedUUIDs)
            except ClusterError:
                logger.warning('Skipping record {}'.format(rec))
                self.updateMatchedRecordsStatus([rec.id])
                self.session.commit()

            if len(indexingWorks) >= 50:
                self.updateElasticSearch(indexingWorks, deletingWorks)
                indexingWorks = []

                self.deleteStaleWorks(deletingWorks)
                deletingWorks = set()

                self.session.commit()

        # Run index/delete methods again for final batch
        self.updateElasticSearch(indexingWorks, deletingWorks)
        self.deleteStaleWorks(deletingWorks)

        self.session.commit()
        self.closeConnection()

    def clusterRecord(self, rec):
        logger.info('Clustering {}'.format(rec))

        self.matchTitleTokens = self.tokenizeTitle(rec.title)

        matchedIDs = self.findAllMatchingRecords(rec.identifiers)

        matchedIDs.append(rec.id)

        clusteredEditions, instances = self.clusterMatchedRecords(matchedIDs)
        dbWork, deletedUUIDs = self.createWorkFromEditions(clusteredEditions, instances)

        try:
            self.session.flush()
        except (DataError, StaleDataError) as e:
            self.session.rollback()
            logger.error('Unable to cluster {}'.format(rec))
            logger.debug(e)

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
        logger.debug('BUILDING WORK')
        workData = recordManager.buildWork(instances, editions)
        logger.debug('SAVING WORK')

        recordManager.saveWork(workData)

        logger.debug('MERGING RECORDS')
        deletedRecordUUIDs = recordManager.mergeRecords()

        return recordManager.work, deletedRecordUUIDs

    def queryIdens(self, idens):
        matchedIDs = set()
        checkedIdens = set()

        checkIdens = idens

        iterations = 0

        while iterations < 4:
            logger.debug('Checking IDS: {}'.format(len(checkIdens)))
            matches = self.getRecordBatches(list(checkIdens), matchedIDs.copy())
            logger.debug('Got Matches: {}'.format(len(matches)))
            if len(matches) == 0:
                break

            checkedIdens.update(checkIdens)
            logger.debug('Checked IDS: {}'.format(len(checkedIdens)))
        
            checkIdens = set()
            for match in matches:
                recTitle, recID, recIdentifiers = match

                if iterations > 0 and self.compareTitleTokens(recTitle):
                    logger.debug('Matched Title Error: {}'.format(recTitle))
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
            logger.debug('Querying Batch {} of {}'.format(ceil(i/100)+1, ceil(len(identifiers)/100)))

            idArray = self.formatIdenArray(identifiers[i:i+step])

            try:
                matches = self.session.query(Record.title, Record.id, Record.identifiers)\
                    .filter(~Record.id.in_(list(matchedIDs)))\
                    .filter(Record.identifiers.overlap(idArray))\
                    .all()

                totalMatches.extend(matches)
            except DataError as e:
                logger.warning('Unable to execute batch id query')
                logger.debug(e)

            i += step
        
        return totalMatches

    def indexWorksInElasticSearch(self, dbWorks):
        esWorks = []

        for dbWork in dbWorks:
            print('Generating ES for {}'.format(dbWork))
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
