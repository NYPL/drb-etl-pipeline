import os
from services import PublisherBacklistService

from ..core import CoreProcess
from logger import create_log
from managers import DBManager, S3Manager
from ..record_buffer import RecordBuffer

logger = create_log(__name__)

class PublisherBacklistProcess(CoreProcess):
    def __init__(self, *args):
        super(PublisherBacklistProcess, self).__init__(*args[:4])

        self.limit = (len(args) >= 5 and args[4] and args(4) <= 100) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manger=self.db_manager)

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

        self.publisher_backlist_service = PublisherBacklistService()
        
    def runProcess(self):
        try:
            self.publisher_backlist_service.delete_records(limit=self.limit)

            if self.process == 'daily':
                records = self.publisher_backlist_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.publisher_backlist_service.get_records(full_import=True)
            elif self.process == 'custom':
                records = self.publisher_backlist_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            else: 
                logger.warning(f'Unknown Publisher Backlist ingestion process type {self.process}')
                return
            
            for record in records:
                self.record_buffer.add(record)
            
            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} Publisher Backlist records')

        except Exception as e:
            logger.exception('Failed to run Publisher Backlist process')
            raise e   
        finally:
            self.db_manager.close_connection()
