import os
from services import DSpaceService

from logger import create_log
from managers import S3Manager, DBManager
from mappings.clacso import CLACSOMapping
from model import FileFlags
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)

class CLACSOProcess():
    CLACSO_BASE_URL = 'https://biblioteca-repositorio.clacso.edu.ar/oai/request?'

    def __init__(self, *args):
        self.process_type = args[0]
        self.ingest_period = args[2]

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(self.db_manager)

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.offset = int(args[5]) if args[5] else 0
        self.limit = (int(args[4]) + self.offset) if args[4] else 10000

        self.dspace_service = DSpaceService(base_url=self.CLACSO_BASE_URL, source_mapping=CLACSOMapping)
        
    def runProcess(self):
        try:
            start_datetime = utils.get_start_datetime(process_type=self.process_type, ingest_period=self.ingest_period)

            records = self.dspace_service.get_records(
                start_timestamp=start_datetime,
                full_import=self.process_type == 'complete',
                offset=self.offset,
                limit=self.limit
            )

            for record_mapping in records:
                self.record_buffer.add(record_mapping.record)
                self.s3_manager.store_pdf_manifest(record_mapping.record, self.s3_bucket, flags=FileFlags())

            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} CLACSO records')
        except Exception as e:
            logger.exception('Failed to run CLACSO process')
            raise e   
        finally:
            self.db_manager.close_connection()
