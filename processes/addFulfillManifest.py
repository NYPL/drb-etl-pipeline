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
        if startTimeStamp:
            filtered_batches = batches.search(f"Contents[?to_string(LastModified) > '\"{startTimeStamp}\"'].Key")
            for batch in filtered_batches:
                for c in batch['Contents']:
                    currKey = c['Key']
                    metadataObject = self.getObjectFromBucket(currKey, self.s3Bucket)
                    self.update_manifest(metadataObject, self.s3Bucket, currKey)
        else:
            for batch in batches:
                for c in batch['Contents']:
                    currKey = c['Key']
                    metadataObject = self.getObjectFromBucket(currKey, self.s3Bucket)
                    self.update_manifest(metadataObject, self.s3Bucket, currKey)

    def update_manifest(self, metadataObject, bucketName, currKey):

        metadataJSON = json.loads(metadataObject['Body'].read().decode("utf-8"))
        metadataJSONCopy = copy.deepcopy(metadataJSON)
        
        counter = 0
    
        metadataJSON, counter = self.linkFulfill(metadataJSON, counter)
        metadataJSON, counter = self.readingOrderFulfill(metadataJSON, counter)
        metadataJSON, counter = self.resourceFulfill(metadataJSON, counter)
        metadataJSON, counter = self.tocFulfill(metadataJSON, counter)

        if counter >= 4: 
            for link in metadataJSON['links']:
                self.fulfillFlagUpdate(link)

        self.closeConnection()

        if metadataJSON != metadataJSONCopy:
            try:
                fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False)
                return self.putObjectInBucket(
                    fulfillManifest, currKey, bucketName
                )
            except ClientError as e:
                logging.error(e)

    def linkFulfill(self, metadataJSON):
        for link in metadataJSON['links']:
            fulfillLink, counter = self.fulfillReplace(link, counter)
            link['href'] = fulfillLink

        return (metadataJSON, counter)
            
    def readingOrderFulfill(self, metadataJSON):
        for readOrder in metadataJSON['readingOrder']:
            fulfillLink, counter = self.fulfillReplace(readOrder, counter)
            readOrder['href'] = fulfillLink

        return (metadataJSON, counter)

    def resourceFulfill(self, metadataJSON):
        for resource in metadataJSON['resources']:
            fulfillLink, counter = self.fulfillReplace(resource, counter)
            resource['href'] = fulfillLink

        return (metadataJSON, counter)

    def tocFulfill(self, metadataJSON): 

        '''
        The toc dictionary has no "type" key like the previous dictionaries 
        therefore the 'href' key is evaluated instead
        '''

        for toc in metadataJSON['toc']:
            if 'pdf' in toc['href'] \
                or 'epub' in toc['href']:
                    for link in self.session.query(Link) \
                        .filter(Link.url == toc['href'].replace('https://', '')):
                            counter += 1
                            toc['href'] = f'http://{self.host}:{self.port}/fulfill/{link.id}'

        return (metadataJSON, counter)

    def fulfillReplace(self, metadata):
        if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
            or metadata['type'] == 'application/epub+xml':
                for link in self.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):
                        counter += 1            
                        metadata['href'] = f'http://{self.host}:{self.port}/fulfill/{link.id}'

        return (metadata['href'], counter)
    
    def fulfillFlagUpdate(self, metadata):
        if metadata['type'] == 'application/webpub+json':
            for link in self.session.query(Link) \
                .filter(Link.url == metadata['href'].replace('https://', '')):   
                        print(link)
                        print(link.flags)
                        if 'fulfill_limited_access' in link.flags.keys():
                            if link.flags['fulfill_limited_access'] == False:
                                newLinkFlag = dict(link.flags)
                                newLinkFlag['fulfill_limited_access'] = True
                                link.flags = newLinkFlag
                                self.commitChanges()

class FulfillError(Exception):
    pass