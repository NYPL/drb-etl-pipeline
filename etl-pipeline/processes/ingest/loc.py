import os

from digital_assets import get_stored_file_url
from managers import DBManager, RabbitMQManager, S3Manager
from model import get_file_message, Part, Record
from logger import create_log
from ..record_buffer import RecordBuffer
from .. import utils
from services import LOCService

logger = create_log(__name__)


class LOCProcess():

    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.loc_service = LOCService()

        self.s3_manager = S3Manager()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.create_connection()
        self.rabbitmq_manager.create_or_connect_queue(self.file_queue, self.file_route)

    def runProcess(self):
        records = self.loc_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
            limit=self.params.limit,
            offset=self.params.offset
        )

        for record in records:
            self.s3_manager.store_pdf_manifest(record=record, bucket_name=self.s3_bucket)
            self.store_epub(record=record)

            self.record_buffer.add(record=record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} LOC records')

    def store_epub(self, record: Record):
        record_id = record.source_id.split('|')[0]
        epub_part = next(filter(lambda part: part.file_type == 'application/epub+zip', record.parts), None)

        if epub_part is not None:
            epub_location = f'epubs/{epub_part.source}/{record_id}.epub'
            epub_url = get_stored_file_url(storage_name=self.s3_bucket, file_path=epub_location)

            record.has_part = [str(Part(
                index=epub_part.index,
                url=epub_url,
                source=record.source,
                file_type=epub_part.file_type,
                flags=epub_part.flags
            ))]

            self.rabbitmq_manager.send_message_to_queue(self.file_queue, self.file_route, get_file_message(epub_part.url, epub_location))
