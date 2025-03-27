import json
import mimetypes
import os
import re

from digital_assets import get_stored_file_url
from mappings.gutenberg import GutenbergMapping
from managers import S3Manager
from model import FileFlags, Part, Source
from logger import create_log
from ..record_file_saver import RecordFileSaver
from services import GutenbergService
from .. import utils

logger = create_log(__name__)


class GutenbergV2Process():
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.file_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

        self.gutenberg_service = GutenbergService()
        self.record_file_saver = RecordFileSaver(storage_manager=self.s3_manager)

    def runProcess(self):
        records = self.gutenberg_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
            offset=self.params.offset,
            limit=self.params.limit,
        )

        for record_mapping in records:
            self.store_epubs(record_mapping)

    def store_epubs(self, gutenberg_record: GutenbergMapping):
        for part in gutenberg_record.record.parts:
            epub_id_parts = re.search(r'\/([0-9]+).epub.([a-z]+)$', part.url)
            gutenberg_id = epub_id_parts.group(1)
            gutenberg_type = epub_id_parts.group(2)

            if json.loads(part.flags).get('download', False) is True:
                epub_path = f'epubs/{part.source}/{gutenberg_id}_{gutenberg_type}.epub'

                try:
                    self.record_file_saver.store_file(file_url=part.url, file_path=epub_path)
                except Exception:
                    logger.info(f'Failed to save files for {gutenberg_record.record}')
