import os
# from services import CLACSOService

from ..core import CoreProcess
from logger import create_log
from managers import S3Manager

logger = create_log(__name__)

class CLACSOProcess(CoreProcess):
    def __init__(self, *args):
        super(CLACSOProcess, self).__init__(*args[:4])

        self.limit = (len(args) >= 5 and args[4] and int(args[4]) <= 100) or None
        self.offset = (len(args) >= 6 and args[5]) or None

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

        # self.clacso_service = CLACSOService()
        
    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            # if self.process == 'daily':
            #     records = self.clacso_service.get_records(offset=self.offset, limit=self.limit)
            # elif self.process == 'complete':
            #     records = self.clacso_service.get_records(full_import=True)
            # elif self.process == 'custom':
            #     records = self.clacso_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            # else: 
            #     logger.warning(f'Unknown CLACSO ingestion process type {self.process}')
            #     return
            # for record in records:
            #     self.addDCDWToUpdateList(record)
            
            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records)} CLACSO records')

        except Exception as e:
            logger.exception('Failed to run CLACSO process')
            raise e   
        finally:
            self.close_connection()