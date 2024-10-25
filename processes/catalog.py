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

    def runProcess(self, max_attempts: int=3):
        self.process_catalog_messages(max_attempts=max_attempts)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Saved {len(self.records)} catalog records')

    def process_catalog_messages(self, max_attempts: int=3):
        for attempt in range(0, max_attempts):
            while message := self.getMessageFromQueue(os.environ['OCLC_QUEUE']):
                message_props, _, message_body = message

                self.process_catalog_message(message_body)
                self.acknowledgeMessageProcessed(message_props.delivery_tag)

            wait_time = 60 * (attempt + 1)
            logger.info(f'Waiting {wait_time}s for OCLC catalog messages')
            sleep(wait_time)

    def process_catalog_message(self, message_body):
        message = json.loads(message_body)
        oclc_number = message.get('oclcNo')
        owi_number = message.get('owiNo')
        
        catalog_record = self.oclcCatalogManager.query_catalog(oclc_number)

        if not catalog_record:
            logger.warning(f'Unable to get catalog record for OCLC number {oclc_number}')
            return
        
        self.parse_catalog_record(catalog_record, oclc_number, owi_number)
        logger.info(f'Processed OCLC catalog query for OCLC number {oclc_number}')

    def parse_catalog_record(self, catalog_record, oclc_number, owi_number):
        try:
            parsed_marc_xml = etree.fromstring(catalog_record.encode('utf-8'))
        except Exception:
            logger.exception(f'Unable to parse OCLC catalog MARC XML for OCLC number: {oclc_number}')
            return

        catalog_record_mapping = CatalogMapping(parsed_marc_xml, { 'oclc': 'http://www.loc.gov/MARC21/slim' }, {})

        try:
            catalog_record_mapping.applyMapping()
            catalog_record_mapping.record.identifiers.append('{}|owi'.format(owi_number))
            
            self.addDCDWToUpdateList(catalog_record_mapping)
        except Exception:
            logger.exception(f'Unable to map OCLC catalog record for OCLC number: {oclc_number}')
