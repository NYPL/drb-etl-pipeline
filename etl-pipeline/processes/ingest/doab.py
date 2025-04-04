import os
from services import DSpaceService
from logger import create_log
from mappings.doab import DOABMapping
from managers import DBManager, DOABLinkManager, S3Manager, RabbitMQManager
from model import get_file_message
from ..record_buffer import RecordBuffer, Record
from .. import utils

logger = create_log(__name__)

class DOABProcess():
    DOAB_BASE_URL = 'https://directory.doabooks.org/oai/request?'
    DOAB_IDENTIFIER = 'oai:directory.doabooks.org'

    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(self.db_manager)

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.create_connection()
        self.rabbitmq_manager.create_or_connect_queue(self.file_queue, self.file_route)

        self.dspace_service = DSpaceService(base_url=self.DOAB_BASE_URL, source_mapping=DOABMapping)

    def runProcess(self):
        try:
            if self.params.record_id is not None:
                record = self.dspace_service.get_single_record(record_id=self.params.record_id, source_identifier=self.DOAB_IDENTIFIER)
                
                self._process_record(record)
                self.record_buffer.flush()
                self._log_results()
                
                return

            records = self.dspace_service.get_records(
                start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
                offset=self.params.offset,
                limit=self.params.limit
            )
                
            for record in records:
                self._process_record(record)
            
            self.record_buffer.flush()

            self._log_results()
        except Exception as e:
            logger.exception('Failed to run DOAB process')
            raise e
        finally:
            self.db_manager.close_connection()

    def manage_links(self, record: Record):
        link_manager = DOABLinkManager(record)

        link_manager.parse_links()

        for manifest in link_manager.manifests:
            manifest_path, manifest_json = manifest
            self.s3_manager.create_manifest_in_s3(
                manifest_path, manifest_json, self.s3_bucket)

        for epub_link in link_manager.epub_links:
            epub_path, epub_uri = epub_link
            self.rabbitmq_manager.send_message_to_queue(self.file_queue, self.file_route, get_file_message(epub_uri, epub_path))

    def _process_record(self, record: Record):
        if record.deletion_flag:
            self.record_buffer.delete(record)
        else:
            self.manage_links(record)
            self.record_buffer.add(record)

    def _log_results(self):
        if self.record_buffer.deletion_count != 0:
            logger.info(f'Deleted {self.record_buffer.deletion_count} DOAB records')
        logger.info(f'Ingested {self.record_buffer.ingest_count} DOAB records')
