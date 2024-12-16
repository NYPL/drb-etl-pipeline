import os
from services import PublisherBacklistService

from ..core import CoreProcess
from logger import create_log
from managers import S3Manager

logger = create_log(__name__)

class PublisherBacklistProcess(CoreProcess):
    def __init__(self, *args):
        super(PublisherBacklistProcess, self).__init__(*args[:4])

        self.limit = (len(args) >= 5 and args[4] and args(4) <= 100) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

        self.publisher_backlist_service = PublisherBacklistService()
        
    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

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
                self.addDCDWToUpdateList(record)
            
            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records)} Publisher Backlist records')

        except Exception as e:
            logger.exception('Failed to run Publisher Backlist process')
            raise e   
        finally:
            self.close_connection()
