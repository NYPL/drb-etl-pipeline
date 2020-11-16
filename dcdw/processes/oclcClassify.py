from datetime import datetime, timedelta
import os

from .core import CoreProcess
from managers import ClassifyManager
from managers.oclcClassify import ClassifyError
from mappings.oclcClassify import ClassifyMapping
from model import Record


class ClassifyProcess(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(ClassifyProcess, self).__init__(process, customFile, ingestPeriod)

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # Redis Connection
        self.createRedisClient()

        # RabbitMQ Connection
        self.createRabbitConnection()
        self.createOrConnectQueue(os.environ['OCLC_QUEUE'])

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
        baseQuery = self.session.query(Record).filter(Record.frbr_status == 'to_do')

        if full is False:
            if not startDateTime:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
            baseQuery = baseQuery.filter(Record.date_modified > startDateTime)
        
        for rec in baseQuery.yield_per(100):
            self.frbrizeRecord(rec)
    
    def frbrizeRecord(self, record):
        for iden in ClassifyManager.getQueryableIdentifiers(record.identifiers):
            identifier, idenType = tuple(iden.split('|'))

            try:
                author, *_ = tuple(record.authors[0].split('|'))
            except IndexError:
                author = None

            if self.checkSetRedis('classify', identifier, idenType) is True:
                record.frbr_status = 'complete'
                self.records.append(record)
                continue

            self.classifyRecordByMetadata(
                identifier, idenType, author, record.title
            )

    def classifyRecordByMetadata(self, identifier, idType, author, title):
        classifier = ClassifyManager(
            iden=identifier, idenType=idType, author=author, title=title
        )

        try:
            xmlRecords = classifier.getClassifyResponse()
        except ClassifyError as err:
            print(err.message)
            return None
        
        for classifyXML in xmlRecords:
            self.createClassifyDCDWRecord(classifyXML, identifier, idType)
    
    def createClassifyDCDWRecord(self, classifyXML, identifier, idType):
        classifyRec = ClassifyMapping(
            classifyXML,
            {'oclc': 'http://classify.oclc.org'},
            {},
            (identifier, idType)
        )
        classifyRec.applyMapping()

        self.addDCDWToUpdateList(classifyRec)

        self.fetchOCLCCatalogRecords(classifyRec.record.identifiers)
    
    def fetchOCLCCatalogRecords(self, identifiers):
        for oclcID in list(filter(lambda x: 'oclc' in x, identifiers)):
            oclcNo, _ = tuple(oclcID.split('|'))
            if self.checkSetRedis('catalog', oclcNo, 'oclc') is False:
                self.sendCatalogLookupMessage(oclcNo)
    
    def sendCatalogLookupMessage(self, oclcNo):
        self.sendMessageToQueue(os.environ['OCLC_QUEUE'], {'oclcNo': oclcNo})
