import json
import os
import newrelic.agent
from lxml import etree
from time import sleep

from .core import CoreProcess
from managers import OCLCCatalogManager
from mappings.oclcCatalog import CatalogMapping
from logger import createLog


logger = createLog(__name__)


class CatalogProcess(CoreProcess):
    def __init__(self, *args):
        super(CatalogProcess, self).__init__(*args[:4], batchSize=50)

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # RabbitMQ Connection
        self.createRabbitConnection()
        self.createChannel()

    def runProcess(self):
        self.receiveAndProcessMessages()

        self.saveRecords()
        self.commitChanges()

    @newrelic.agent.background_task()
    def receiveAndProcessMessages(self):
        attempts = 1

        while True:
            msgProps, _, msgBody = self.getMessageFromQueue(
                os.environ['OCLC_QUEUE']
            )

            if msgProps is None:
                if attempts <= 3:
                    waitTime = 60 * attempts

                    logger.info('Waiting {}s for addtl recs'.format(waitTime))

                    sleep(waitTime)

                    attempts += 1

                    continue
                else:
                    logger.info('No messages to process, exiting')
                    break

            attempts = 1  # Reset attempt counter for further batches

            self.processCatalogQuery(msgBody)
            self.acknowledgeMessageProcessed(msgProps.delivery_tag)

    @newrelic.agent.background_task()
    def processCatalogQuery(self, msgBody):
        message = json.loads(msgBody)
        catalogManager = OCLCCatalogManager(message['oclcNo'])
        catalogXML = catalogManager.queryCatalog()
        if catalogXML:
            self.parseCatalogRecord(catalogXML, message['owiNo'])


    @newrelic.agent.background_task()
    def parseCatalogRecord(self, catalogXML, owiNo):
        try:
            parseMARC = etree.fromstring(catalogXML.encode('utf-8'))
        except etree.XMLSyntaxError as err:
            logger.error('OCLC Catalog returned invalid XML')
            logger.debug(err)
            return None

        catalogRec = CatalogMapping(
            parseMARC,
            {'oclc': 'http://www.loc.gov/MARC21/slim'},
            {}
        )

        try:
            catalogRec.applyMapping()
            catalogRec.record.identifiers.append('{}|owi'.format(owiNo))
            self.addDCDWToUpdateList(catalogRec)
        except Exception as err:
            logger.error('Err querying OCLC Rec {}'.format(
                catalogRec.record.source_id
            ))
            logger.debug(err)
