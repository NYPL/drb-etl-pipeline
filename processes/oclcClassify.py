from datetime import datetime, timedelta, timezone
import os
import newrelic.agent

from .core import CoreProcess
from managers import OCLCCatalogManager
from managers.oclc_catalog import OCLCError
from managers import catalog_utils
from model import Record
from logger import createLog


logger = createLog(__name__)


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

        self.classifiedRecords = {}

    def runProcess(self):
        if self.process == 'daily':
            self.classifyRecords()
        elif self.process == 'complete':
            self.classifyRecords(full=True)
        elif self.process == 'custom':
            self.classifyRecords(startDateTime=self.ingestPeriod)

        self.saveRecords()
        self.updateClassifiedRecordsStatus()
        self.commitChanges()

    def classifyRecords(self, full=False, startDateTime=None):
        baseQuery = self.session.query(Record)\
            .filter(
                Record.source != 'oclcClassify'
                and Record.source != 'oclcCatalog'
            )\
            .filter(Record.frbr_status == 'to_do')

        if full is False:
            if not startDateTime:
                startDateTime = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            baseQuery = baseQuery.filter(Record.date_modified > startDateTime)

        windowSize = self.ingestLimit
        if (self.ingestLimit is None or self.ingestLimit > 100):
            windowSize = 100

        for rec in self.windowedQuery(
            Record, baseQuery, windowSize=windowSize
        ):
            self.frbrizeRecord(rec)

            # Update Record with status
            rec.cluster_status = False
            rec.frbr_status = 'complete'
            self.classifiedRecords[rec.id] = rec

            if self.checkIncrementerRedis('oclcCatalog', 'API'):
                logger.warning('Exceeded max requests to OCLC catalog')
                break

            if len(self.classifiedRecords) >= windowSize:
                logger.debug('Storing classified records')
                self.updateClassifiedRecordsStatus()
                self.classifiedRecords = {}

    def updateClassifiedRecordsStatus(self):
        self.bulkSaveObjects([r for _, r in self.classifiedRecords.items()])

    def frbrizeRecord(self, record):
        queryableIDs = ClassifyManager.getQueryableIdentifiers(
            record.identifiers
        )

        if len(queryableIDs) < 1:
            queryableIDs = [None]

        for iden in queryableIDs:
            try:
                identifier, idenType = tuple(iden.split('|'))
            except AttributeError:
                identifier, idenType = (None, None)

            try:
                author, *_ = tuple(record.authors[0].split('|'))
            except (IndexError, TypeError):
                author = None

            # Check if this identifier has been queried in the past 24 hours
            # Skip if it has already been looked up
            if identifier and self.checkSetRedis(
                'classify', identifier, idenType
            ):
                continue

            try:
                self.classifyRecordByMetadata(
                    identifier, idenType, author, record.title
                )
            except ClassifyError as err:
                logger.warning('Unable to Classify {}'.format(record))
                logger.debug(err.message)

    def classifyRecordByMetadata(self, identifier, idType, author, title):
        classifier = ClassifyManager(
            iden=identifier, idenType=idType, author=author, title=title
        )

        for classifyXML in classifier.getClassifyResponse():
            if self.checkIfClassifyWorkFetched(classifyXML) is True:
                logger.info(
                    'Skipping Duplicate Classify Record {} ({}:{})'.format(
                        title, identifier, idType
                    )
                )
                continue

            classifier.checkAndFetchAdditionalEditions(classifyXML)

            self.createClassifyDCDWRecord(
                classifyXML, classifier.addlIds, identifier, idType
            )

    def createClassifyDCDWRecord(
        self, classifyXML, additionalOCLCs, identifier, idType
    ):
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

        counter = 0
        oclcIDs = set()
        for oclcID in list(filter(lambda x: 'oclc' in x, identifiers)):
            oclcNo, _ = tuple(oclcID.split('|'))
            oclcIDs.add(oclcNo)

        oclcIDs = list(oclcIDs)

        checkedIDs = self.multiCheckSetRedis('catalog', oclcIDs, 'oclc')

        for oclcNo, updateReq in checkedIDs:
            if updateReq is False:
                continue

            self.sendCatalogLookupMessage(oclcNo, owiNo)
            counter += 1

        if counter > 0:
            self.setIncrementerRedis('oclcCatalog', 'API', amount=counter)

    def sendCatalogLookupMessage(self, oclcNo, owiNo):
        logger.debug('Sending OCLC# {} to queue'.format(oclcNo))
        self.sendMessageToQueue(
            self.rabbitQueue,
            self.rabbitRoute,
            {'oclcNo': oclcNo, 'owiNo': owiNo}
        )

    def checkIfClassifyWorkFetched(self, classifyXML):
        workOWI = classifyXML.find(
            './/work', namespaces=ClassifyManager.NAMESPACE
        ).attrib['owi']

        return self.checkSetRedis('classifyWork', workOWI, 'owi')
