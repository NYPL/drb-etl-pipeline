import os
from services import DSpaceService
from ..core import CoreProcess
from logger import create_log
from mappings.doab import DOABMapping
from managers import DOABLinkManager, S3Manager, RabbitMQManager
from model import get_file_message

logger = create_log(__name__)

class DOABProcess(CoreProcess):
    DOAB_BASE_URL = 'https://directory.doabooks.org/oai/request?'
    DOAB_IDENTIFIER = 'oai:directory.doabooks.org'

    def __init__(self, *args):
        super(DOABProcess, self).__init__(*args[:4])

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
            self.generateEngine()
            self.createSession()

            records = []

            if self.process == 'daily':
                records = self.dspace_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.dspace_service.get_records(full_import=True, offset=self.offset, limit=self.limit)
            elif self.process == 'custom':
                records = self.dspace_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            elif self.singleRecord:
                record = self.dspace_service.get_single_record(record_id=self.singleRecord, source_identifier=self.DOAB_IDENTIFIER)
                self.manage_links(record)

            if records:
                for record in records:
                    self.manage_links(record)

            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records) if records else 1} DOAB records')

        except Exception as e:
            logger.exception('Failed to run DOAB process')
            raise e
        finally:
            self.close_connection()

    def manage_links(self, record):
        linkManager = DOABLinkManager(record.record)

        linkManager.parseLinks()

        for manifest in linkManager.manifests:
            manifestPath, manifestJSON = manifest
            self.s3_manager.createManifestInS3(
                manifestPath, manifestJSON, self.s3_bucket)

        for epubLink in linkManager.ePubLinks:
            ePubPath, ePubURI = epubLink
            self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(ePubURI, ePubPath))

        self.addDCDWToUpdateList(record)
