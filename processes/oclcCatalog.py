import json
import os
from lxml import etree
from time import sleep

from .core import CoreProcess
from managers import OCLCCatalogManager
from mappings.oclcCatalog import CatalogMapping
from logging import logger


class CatalogProcess(CoreProcess):
    def __init__(self, *args):
        super(CatalogProcess, self).__init__(*args[:4], batchSize=50)

        self.generateEngine()
        self.createSession()

        self.createRabbitConnection()
        self.createChannel()

        self.oclcCatalogManager = OCLCCatalogManager()

    def runProcess(self, max_attempts: int=3):
        self.receiveAndProcessMessages(max_attempts=max_attempts)

        self.saveRecords()
        self.commitChanges()

    def receiveAndProcessMessages(self, max_attempts: int=3):
        attempts = 1

        while True:
            msgProps, _, msgBody = self.getMessageFromQueue(os.environ['OCLC_QUEUE'])

            if msgProps is None:
                if attempts <= max_attempts:
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
            logger.warning(f'Unable to get catalog XML for OCLC number {oclcNo}')
            return
        
        self.parseCatalogRecord(catalogXML, oclcNo, owiNo)
        logger.info(f'Processed OCLC catalog query for OCLC number {oclcNo}')

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
