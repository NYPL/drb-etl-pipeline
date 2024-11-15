import os
from ..util import airtable_integration

from ..core import CoreProcess
from logger import create_log

logger = create_log(__name__)

class PublisherBacklistProcess(CoreProcess):
    def __init__(self, *args):
        super(PublisherBacklistProcess, self).__init__(*args[:4])

        self.ingest_offset = int(args[5] or 0)
        self.ingest_limit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.full_import = self.process == 'complete' 

        self.generateEngine()
        self.createSession()

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def runProcess(self):
        try:

            response = airtable_integration.create_airtable_request()
            
            print(response)

        except Exception as e:
            logger.exception('Failed to run Pub Backlist process')
            raise e
    