import json
import os
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

        self.generateEngine()
        self.createSession()

        self.createRabbitConnection()
        self.createChannel()

        self.oclcCatalogManager = OCLCCatalogManager()

    def runProcess(self):
        self.receiveAndProcessMessages()

        self.saveRecords()
        self.commitChanges()

    def receiveAndProcessMessages(self):
        attempts = 1

        while True:
            msgProps, _, msgBody = self.getMessageFromQueue(os.environ['OCLC_QUEUE'])

            if msgProps is None:
                if attempts <= 3:
                    waitTime = 60 * attempts

                    logger.info(f'Waiting {waitTime}s for OCLC catalog messages')

                    sleep(waitTime)

                    attempts += 1

                    continue
                else:
                    logger.info('Exiting OCLC catalog process - no more messages.')
                    break

            attempts = 1

            self.processCatalogQuery(msgBody)
            self.acknowledgeMessageProcessed(msgProps.delivery_tag)

    def processCatalogQuery(self, msgBody):
        message = json.loads(msgBody)
        oclcNo = message.get('oclcNo')
        owiNo = message.get('owiNo')
        
        catalogXML = self.oclcCatalogManager.query_catalog(oclcNo)

        if not catalogXML:
            return
        
        self.parseCatalogRecord(catalogXML, oclcNo, owiNo)


    def parseCatalogRecord(self, catalogXML, oclcNo, owiNo):
        try:
            parseMARC = etree.fromstring(catalogXML.encode('utf-8'))
        except etree.XMLSyntaxError as e:
            logger.error(f'OCLC catalog MARC xml is invalid for OCLC number: {oclcNo}')
            logger.debug(e)
            return

        catalogRec = CatalogMapping(
            parseMARC,
            {'oclc': 'http://www.loc.gov/MARC21/slim'},
            {}
        )

        try:
            catalogRec.applyMapping()
            catalogRec.record.identifiers.append('{}|owi'.format(owiNo))
            self.addDCDWToUpdateList(catalogRec)
        except Exception as e:
            logger.error(
                f'Unable to parse OCLC catalog record with id {catalogRec.record.source_id} due to {e}'
            )
            logger.debug(e)
