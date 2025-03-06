import os
from services import PublisherBacklistService

from logger import create_log
from managers import DBManager, S3Manager
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)

class PublisherBacklistProcess():
    def __init__(self, *args):
        self.process = args[1]
        self.ingest_period = args[2]

        self.limit = (len(args) >= 5 and args[4] and int(args[4]) <= 100) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

        self.publisher_backlist_service = PublisherBacklistService()
        
    def runProcess(self):
        try:
            start_datetime = utils.get_start_datetime(process_type=self.process, ingest_period=self.ingest_period)
            self.publisher_backlist_service.delete_records()

            records = self.publisher_backlist_service.get_records(
                start_timestamp=start_datetime,
                offset=self.offset,
                limit=self.limit
            )
            
            for record_mapping in records:
                self.record_buffer.add(record_mapping.record)
            
            self.record_buffer.flush()

            logger.info(f'Ingested {len(self.records)} Publisher Backlist records')
        except Exception as e:
            logger.exception('Failed to run Publisher Backlist process')
            raise e   
        finally:
            self.db_manager.close_connection()
