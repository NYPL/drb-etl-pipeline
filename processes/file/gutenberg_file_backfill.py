import json
from multiprocessing import Pool
import os
import re

from model import Record
from mappings.gutenberg import GutenbergMapping
from managers import S3Manager
from logger import create_log
from ..record_file_saver import RecordFileSaver
from services import GutenbergService
from .. import utils

logger = create_log(__name__)


class GutenbergFileBackfill:
    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)
        self.gutenberg_service = GutenbergService()

    def runProcess(self):
        records = self.gutenberg_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
            offset=self.params.offset,
            limit=self.params.limit,
            record_only=True
        )

        with Pool(processes=4) as pool:
            file_backfill_results = pool.imap_unordered(GutenbergFileBackfill._store_epubs, records)
            file_backfills = [result for result in file_backfill_results]
            successful_file_backfills = len([result for result in file_backfills if result is True])

        logger.info(f'Stored {successful_file_backfills}/{len(file_backfills)} Gutenberg record files')

    @staticmethod
    def _store_epubs(record: Record):
        file_bucket = os.environ.get('FILE_BUCKET')
        s3_manager = S3Manager()
        s3_manager.createS3Client()
        record_file_saver = RecordFileSaver(storage_manager=s3_manager)
        saved_files = True

        for part in record.parts:
            epub_id_parts = re.search(r'\/([0-9]+).epub.([a-z]+)$', part.url)
            gutenberg_id = epub_id_parts.group(1)
            gutenberg_type = epub_id_parts.group(2)

            if json.loads(part.flags).get('download', False) is True:
                epub_path = f'epubs/{part.source}/{gutenberg_id}_{gutenberg_type}.epub'

                try:
                    record_file_saver.store_file(file_url=part.url, file_path=epub_path)
                    s3_manager.s3Client.head_object(Bucket=file_bucket, Key=epub_path)            
                except Exception:
                    logger.info(f'Failed to save {part.url} for {record}')
                    saved_files = False
                
        return saved_files
