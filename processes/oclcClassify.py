from datetime import datetime, timedelta
import os

from .core import CoreProcess
from managers import ClassifyManager
from managers.oclcClassify import ClassifyError
from mappings.oclcClassify import ClassifyMapping
from model import Record


class ClassifyProcess(CoreProcess):
    def __init__(self, *args):
        super(ClassifyProcess, self).__init__(*args[:4], batchSize=50)

        self.ingestLimit = int(args[4]) if args[4] else None

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # Redis Connection
        self.createRedisClient()

        # RabbitMQ Connection
        self.rabbitQueue = os.environ['OCLC_QUEUE']
        self.rabbitRoute = os.environ['OCLC_ROUTING_KEY']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.rabbitQueue, self.rabbitRoute)

    def runProcess(self):
        if self.process == 'daily':
            self.classifyRecords()
        elif self.process == 'complete':
            self.classifyRecords(full=True)
        elif self.process == 'custom':
            self.classifyRecords(startDateTime=self.ingestPeriod)

        self.saveRecords()
        self.commitChanges()
    
    def classifyRecords(self, full=False, startDateTime=None):
        baseQuery = self.session.query(Record)\
            .filter(Record.source != 'oclcClassify')\
            .filter(Record.frbr_status == 'to_do')

        if full is False:
            if not startDateTime:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
            baseQuery = baseQuery.filter(Record.date_modified > startDateTime)

        windowSize = 100 if (self.ingestLimit is None or self.ingestLimit > 100) else self.ingestLimit
        for rec in self.windowedQuery(Record, baseQuery, windowSize=windowSize):
            self.frbrizeRecord(rec)

            self.session.query(Record)\
                .filter(Record.id == rec.id)\
                .update({'cluster_status': False, 'frbr_status': 'complete'}, synchronize_session='fetch')

    def frbrizeRecord(self, record):
        for iden in ClassifyManager.getQueryableIdentifiers(record.identifiers):
            identifier, idenType = tuple(iden.split('|'))

            try:
                author, *_ = tuple(record.authors[0].split('|'))
            except IndexError:
                author = None

            # Check if this identifier has been queried in the past 24 hours
            # Skip if it has already been looked up
            if self.checkSetRedis('classify', identifier, idenType): continue

            try:
                self.classifyRecordByMetadata(
                    identifier, idenType, author, record.title
                )
            except ClassifyError as err:
                print(err.message)

    def classifyRecordByMetadata(self, identifier, idType, author, title):
        classifier = ClassifyManager(
            iden=identifier, idenType=idType, author=author, title=title
        )

        for classifyResult in classifier.getClassifyResponse():
            self.createClassifyDCDWRecord(classifyResult, identifier, idType)
    
    def createClassifyDCDWRecord(self, classifyResult, identifier, idType):
        classifyXML, additionalOCLCs = classifyResult
        classifyRec = ClassifyMapping(
            classifyXML,
            {'oclc': 'http://classify.oclc.org'},
            {},
            (identifier, idType)
        )
        classifyRec.applyMapping()

        classifyRec.extendIdentifiers(additionalOCLCs)

        self.addDCDWToUpdateList(classifyRec)

        self.fetchOCLCCatalogRecords(classifyRec.record.identifiers)
    
    def fetchOCLCCatalogRecords(self, identifiers):
        owiNo, _ = tuple(identifiers[0].split('|'))

        for oclcID in list(filter(lambda x: 'oclc' in x, identifiers)):
            oclcNo, _ = tuple(oclcID.split('|'))
            if self.checkSetRedis('catalog', oclcNo, 'oclc') is False:
                self.sendCatalogLookupMessage(oclcNo, owiNo)
    
    def sendCatalogLookupMessage(self, oclcNo, owiNo):
        self.sendMessageToQueue(
            self.rabbitQueue, self.rabbitRoute, {'oclcNo': oclcNo, 'owiNo': owiNo}
        )
