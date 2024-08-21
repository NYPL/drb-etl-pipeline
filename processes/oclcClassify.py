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

        self.oclc_manager = OCLCCatalogManager()

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
            self.frbrize_record(rec)

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

    def frbrize_record(self, record):
        queryable_ids = catalog_utils.get_queryable_identifiers(
            record.identifiers
        )

        if len(queryable_ids) < 1:
            queryable_ids = [None]

        for iden in queryable_ids:
            try:
                identifier, iden_type = tuple(iden.split('|'))
            except AttributeError:
                identifier, iden_type = (None, None)

            try:
                author, *_ = tuple(record.authors[0].split('|'))
            except (IndexError, TypeError):
                author = None

            # Check if this identifier has been queried in the past 24 hours
            # Skip if it has already been looked up
            if identifier and self.checkSetRedis(
                'classify', identifier, iden_type
            ):
                continue

            try:
                self.classify_record_by_metadata(
                    identifier, iden_type, author, record.title
                )
            except OCLCError as err:
                logger.warning(f'Unable to retrieve {record} record from OCLC')
                logger.debug(err.message)

    def classify_record_by_metadata(self, identifier, id_type, author, title):
        query = self.oclc_manager.generate_search_query(identifier=identifier,
                                                        identifier_type=id_type,
                                                        author=author,
                                                        title=title)
        for bib in self.oclc_manager.query_brief_bibs(query)['briefRecords']:
            if self.check_if_bib_already_retrieved(bib) is True:
                logger.info(
                    f'Skipping already retrieved record {title} ({identifier}:{id_type})'
                )
                continue

            additional_ids = self.oclc_manager.get_related_oclc_numbers(bib['oclcNumber'])

            # TODO: Should we persist the bibs we get to the database and how?
            # The DCDW save method below is what previously passed the additional OCLC nos
            # from above to the catalog process.
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

        self.fetch_oclc_catalog_records(classifyRec.record.identifiers)

    def fetch_oclc_catalog_records(self, identifiers):
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

            self.send_catalog_lookup_message(oclcNo, owiNo) # where do we get owi?
            counter += 1

        if counter > 0:
            self.setIncrementerRedis('oclcCatalog', 'API', amount=counter)

    def send_catalog_lookup_message(self, oclcNo, owiNo):
        logger.debug('Sending OCLC# {} to queue'.format(oclcNo))
        self.sendMessageToQueue(
            self.rabbitQueue,
            self.rabbitRoute,
            {'oclcNo': oclcNo, 'owiNo': owiNo}
        )

    def check_if_bib_already_retrieved(self, bib):
        # TODO: This code should check if the OCLC Work has already been cached
        # during this run of this process. I am guessing we may need to tweak
        # resources in redis rather than reusing existing Classify tables/indices?

        #workOWI = classifyXML.find(
        #    './/work', namespaces=ClassifyManager.NAMESPACE
        #).attrib['owi']

        return False # self.checkSetRedis('classifyWork', workOWI, 'owi')
