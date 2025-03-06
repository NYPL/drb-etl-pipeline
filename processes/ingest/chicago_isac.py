import json
import os
import traceback
import dataclasses

from mappings.chicago_isac import map_chicago_isac_record
from managers import DBManager, S3Manager, WebpubManifest
from model import Record, Part, FileFlags
from logger import create_log
from ..record_buffer import RecordBuffer
from digital_assets import get_stored_file_url

logger = create_log(__name__)

class ChicagoISACProcess():
    def __init__(self, *args):
        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(self.db_manager)

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):    
        with open('ingestJSONFiles/chicagoISAC_metadata.json') as f:
            chicago_isac_data = json.load(f)

        for dcdw_record in self.process_chicago_isac_records(records=chicago_isac_data):
            self.record_buffer.add(dcdw_record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} ISAC records')

    def process_chicago_isac_records(self, records: list[dict]):
        for record in records:
            try:
                dcdw_record = map_chicago_isac_record(record)

                if dcdw_record is None:
                    continue

                self.s3_manager.store_pdf_manifest(dcdw_record, bucket_name=self.s3_bucket)
                
                yield dcdw_record
            except Exception:
                logger.exception(f"Unable to process ISAC record: {record.get('title')}")
                print(traceback.print_exc())
