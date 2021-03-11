from datetime import datetime, timedelta
from math import ceil
import re

from .core import CoreProcess
from managers import SFRRecordManager, KMeansManager, SFRElasticRecordManager
from model import Record
from logger import createLog

logger = createLog(__name__)


class ClusterProcess(CoreProcess):
    def __init__(self, *args):
        super(ClusterProcess, self).__init__(*args[:4])

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # Redis Connection
        self.createRedisClient()

        # ElasticSearch Connection
        self.createElasticConnection()
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
            .filter(Record.cluster_status == False)

        if full is False:
            if not startDateTime:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
            baseQuery = baseQuery.filter(Record.date_modified > startDateTime)
        
        while True:
            rec = baseQuery.first()

            if rec is None:
                break

            self.clusterRecord(rec)

        self.closeConnection()

    def clusterRecord(self, rec):
        logger.info('Clustering {}'.format(rec))
        matchedIDs = self.findAllMatchingRecords(rec.identifiers)

        filterParams = None
        if len(matchedIDs) < 1:
            filterParams = Record.uuid == rec.uuid
            matchedIDs = [rec.id]
        else:
            filterParams = Record.id.in_(matchedIDs)

        clusteredEditions, instances = self.clusterMatchedRecords(matchedIDs)
        dbWork = self.createWorkFromEditions(clusteredEditions, instances)
        self.session.flush()

        self.indexWorkInElasticSearch(dbWork)

        self.session.query(Record)\
            .filter(filterParams)\
            .update(
                {'cluster_status': True, 'frbr_status': 'complete'},
                synchronize_session='fetch'
            )

        self.commitChanges()

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
        recordManager = SFRRecordManager(self.session)
        workData = recordManager.buildWork(instances, editions)
        recordManager.saveWork(workData)
        recordManager.mergeRecords()

        return recordManager.work
    
    def queryIdens(self, idens):
        matchedIDs = set()
        checkedIdens = set()

        checkIdens = set(filter(None, [
            i if self.checkSetRedis('cluster', i, 'all') is False else None
            for i in idens
        ]))

        iterations = 0

        while iterations < 3:
            logger.debug('Checking IDS: {}'.format(len(checkIdens)))
            matches = self.getRecordBatches(list(checkIdens), matchedIDs.copy())
            logger.debug('Got Matches: {}'.format(len(matches)))
            if len(matches) == 0:
                break

            checkedIdens.update(checkIdens)
            logger.debug('Checked IDS: {}'.format(len(checkedIdens)))
        
            checkIdens = set()
            for match in matches:
                recID, recIdentifiers = match
                checkIdens.update(list(filter(
                    lambda x: re.search(r'\|(?:isbn|issn|oclc|lccn|owi)$', x) != None and x not in checkedIdens,
                    recIdentifiers)
                ))
                matchedIDs.add(recID)

            iterations += 1

        return list(matchedIDs)

    def getRecordBatches(self, identifiers, matchedIDs):
        step = 100 
        i = 0
        totalMatches = []

        while i < len(identifiers):
            logger.debug('Querying Batch {} of {}'.format(ceil(i/100)+1, ceil(len(identifiers)/100)))
            idArray = '{{{}}}'.format(','.join(identifiers[i:i+step]))
            matches = self.session.query(Record.id, Record.identifiers)\
                .filter(~Record.id.in_(list(matchedIDs)))\
                .filter(Record.identifiers.overlap(idArray))\
                .all()

            totalMatches.extend(matches)

            i += step
        
        return totalMatches

    def indexWorkInElasticSearch(self, dbWork):
        elasticManager = SFRElasticRecordManager(dbWork)
        elasticManager.getCreateWork()
        elasticManager.saveWork()
