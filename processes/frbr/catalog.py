import json
import os
from lxml import etree
from time import sleep

from ..core import CoreProcess
from managers import DBManager, OCLCCatalogManager, RabbitMQManager
from mappings.oclcCatalog import CatalogMapping
from logger import create_log
from ..record_buffer import RecordBuffer


logger = create_log(__name__)


class CatalogProcess(CoreProcess):
    def __init__(self, *args):
        super(CatalogProcess, self).__init__(*args[:4])

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager, batch_size=50)

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createChannel()

        self.oclc_catalog_manager = OCLCCatalogManager()

    def runProcess(self, max_attempts: int=4):
        self.process_catalog_messages(max_attempts=max_attempts)

        self.record_buffer.flush()

        logger.info(f'Saved {self.record_buffer.ingest_count} catalog records')

    def process_catalog_messages(self, max_attempts: int=4):
        for attempt in range(0, max_attempts):
            wait_time = 60 * attempt

            if wait_time:
                logger.info(f'Waiting {wait_time}s for OCLC catalog messages')
                sleep(wait_time)

            while message := self.rabbitmq_manager.getMessageFromQueue(os.environ['OCLC_QUEUE']):
                message_props, _, message_body = message

                if not message_props or not message_body:
                    break

                self.process_catalog_message(message_body)
                self.rabbitmq_manager.acknowledgeMessageProcessed(message_props.delivery_tag)

    def process_catalog_message(self, message_body):
        message = json.loads(message_body)
        oclc_number = message.get('oclcNo')
        owi_number = message.get('owiNo')
        
        catalog_record = self.oclc_catalog_manager.query_catalog(oclc_number)

        if not catalog_record:
            logger.warning(f'Unable to get catalog record for OCLC number {oclc_number}')
            return
        
        self.parse_catalog_record(catalog_record, oclc_number, owi_number)

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
            
            self.record_buffer.add(catalog_record_mapping)
        except Exception:
            logger.exception(f'Unable to map OCLC catalog record for OCLC number: {oclc_number}')
