import json
import os
import copy
import logging
from botocore.exceptions import ClientError

from .core import CoreProcess
from datetime import datetime, timedelta, timezone
from model import Link
from logger import createLog

logger = createLog(__name__)

class FulfillProcess(CoreProcess):

    def __init__(self, *args):
        super(FulfillProcess, self).__init__(*args[:4])

        self.fullImport = self.process == 'complete' 
        self.startTimestamp = None

        # Connect to database
        self.generateEngine()
        self.createSession()

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']
        self.host = os.environ['DRB_API_HOST']
        self.port = os.environ['DRB_API_PORT']
        self.prefix = 'manifests/UofM/'
        self.createS3Client()

    def runProcess(self):
        if self.process == 'daily':
            startTimeStamp = datetime.now(timezone.utc) - timedelta(days=1)
            self.getManifests(startTimeStamp)
        elif self.process == 'complete':
            self.getManifests()
        elif self.process == 'custom':
            timeStamp = self.ingestPeriod
            startTimeStamp = datetime.strptime(timeStamp, '%Y-%m-%dT%H:%M:%S')
            self.getManifests(startTimeStamp)

    def getManifests(self, startTimeStamp=None):

        '''Load batch of LA works based on startTimeStamp'''

        batches = self.load_batches(self.prefix, self.s3Bucket)
        filtered_batches = batches.search(f"Contents[?to_string(LastModified) > '\"{startTimeStamp}\"'].Key")
        for batch in filtered_batches:
            currKey = batch['Key']
            metadataObject = self.getObjectFromBucket(currKey, self.s3Bucket)
            self.update_manifest(metadataObject, self.s3Bucket, currKey)

    def update_manifest(self, metadataObject, bucketName, currKey):

        metadataJSON = json.loads(metadataObject['Body'].read().decode("utf-8"))
        metadataJSONCopy = copy.deepcopy(metadataJSON)
        
        metadataJSON = self.linkFulfill(metadataJSON)
        metadataJSON = self.readingOrderFulfill(metadataJSON)
        metadataJSON = self.resourceFulfill(metadataJSON)
        metadataJSON = self.tocFulfill(metadataJSON)

        if metadataJSON != metadataJSONCopy:
            try:
                fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False)
                return self.putObjectInBucket(
                    fulfillManifest, currKey, bucketName
                )
            except ClientError as e:
                logging.error(e)
        
        self.closeConnection()

    def linkFulfill(self, metadataJSON):
        for link in metadataJSON['links']:
            link['href'] = self.fulfillReplace(self, link)

        return metadataJSON
            
    def readingOrderFulfill(self, metadataJSON):
        for readOrder in metadataJSON['readingOrder']:
            readOrder['href'] = self.fulfillReplace(self, readOrder)

        return metadataJSON

    def resourceFulfill(self, metadataJSON):
        for resource in metadataJSON['resources']:
            resource['href'] = self.fulfillReplace(self, resource)

        return metadataJSON

    def tocFulfill(self, metadataJSON): 

        '''
        THe toc dictionary has no "type" key like the previous dictionaries 
        therefore the 'href' key is evaluated instead
        '''

        for toc in metadataJSON['toc']:
            if 'pdf' in toc['href'] \
                or 'epub' in toc['href']:
                    for link in self.session.query(Link) \
                        .filter(Link.url == toc['href'].replace('https://', '')):
                            toc['href'] = f'{self.host}:{self.port}/fulfill/{link.id}'
                            link.flags['fulfill_limited_access'] = True
        return metadataJSON

    def fulfillReplace(self, metadata):
        if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
            or metadata['type'] == 'application/epub+xml':
                for link in self.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):
                        metadata['href'] = f'{self.host}:{self.port}/fulfill/{link.id}'
                        link.flags['fulfill_limited_access'] = True
        return metadata['href']

class FulfillError(Exception):
    pass