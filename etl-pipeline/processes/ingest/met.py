import os
from typing import Optional

from digital_assets import get_stored_file_url
from managers import DBManager, RabbitMQManager, S3Manager
from model import get_file_message, Record, Part, FileFlags, Source
from logger import create_log
from ..record_buffer import RecordBuffer
from services import METService
from .. import utils

logger = create_log(__name__)


class METProcess():
    
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.met_service = METService()

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

    def runProcess(self):
        records = self.met_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
            limit=self.params.limit,
            offset=self.params.offset
        )

        for record in records:
            self.s3_manager.store_pdf_manifest(record=record, bucket_name=self.s3_bucket)
            self.record_buffer.add(record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} MET records')
