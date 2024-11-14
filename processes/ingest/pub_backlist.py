import os
import requests
from ..util import airtable_authentication

from ..core import CoreProcess
from logger import createLog

logger = createLog(__name__)

class PubBacklistProcess(CoreProcess):
    def __init__(self, *args):
        super(PubBacklistProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete' 

        self.generateEngine()
        self.createSession()

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def runProcess(self):
        try:
            headers = airtable_authentication.create_authorization_header()

            response = requests.get('https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&maxRecords=3', headers=headers)

            print(response.json())

        except Exception as e:
            logger.exception('Failed to run Pub Backlist process')
            raise e
        