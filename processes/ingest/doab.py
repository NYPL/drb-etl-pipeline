import os
from services import DSpaceService
from logger import create_log
from mappings.doab import DOABMapping
from managers import DBManager, DOABLinkManager, S3Manager, RabbitMQManager
from model import get_file_message
from .record_buffer import RecordBuffer

logger = create_log(__name__)

class DOABProcess():
    DOAB_BASE_URL = 'https://directory.doabooks.org/oai/request?'
    DOAB_IDENTIFIER = 'oai:directory.doabooks.org'

    def __init__(self, *args):
        self.process = args[0]
        self.ingest_period = args[2]
        self.single_record = args[3]

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(self.db_manager)

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(
            self.file_queue, self.file_route)

        self.offset = int(args[5]) if args[5] else 0
        self.limit = (int(args[4]) + self.offset) if args[4] else 10000

        self.dspace_service = DSpaceService(base_url=self.DOAB_BASE_URL, source_mapping=DOABMapping)

    def runProcess(self):
        try:
            records = []

            if self.process == 'daily':
                records = self.dspace_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.dspace_service.get_records(full_import=True, offset=self.offset, limit=self.limit)
            elif self.process == 'custom':
                records = self.dspace_service.get_records(start_timestamp=self.ingest_period, offset=self.offset, limit=self.limit)
            elif self.single_record:
                record = self.dspace_service.get_single_record(record_id=self.single_record, source_identifier=self.DOAB_IDENTIFIER)
                self.manage_links(record)
                self.record_buffer.add(record.record)

            if records:
                for record in records:
                    self.manage_links(record)
                    self.record_buffer.add(record.record)
            
            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} DOAB records')

        except Exception as e:
            logger.exception('Failed to run DOAB process')
            raise e
        finally:
            self.db_manager.close_connection()

    def manage_links(self, record):
        linkManager = DOABLinkManager(record.record)

        linkManager.parseLinks()

        for manifest in linkManager.manifests:
            manifestPath, manifestJSON = manifest
            self.s3_manager.create_manifest_in_s3(
                manifestPath, manifestJSON, self.s3_bucket)

        for epubLink in linkManager.ePubLinks:
            ePubPath, ePubURI = epubLink
            self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(ePubURI, ePubPath))
