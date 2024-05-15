import json
import os
import boto3
import copy
import logging
from requests.exceptions import HTTPError, ConnectionError
from botocore.exceptions import ClientError

from .core import CoreProcess
from urllib.error import HTTPError
from managers import WebpubManifest
from datetime import datetime, timedelta, timezone
from managers import DBManager
from model import Link
from logger import createLog

logger = createLog(__name__)

s3_client = boto3.client("s3")
bucketName = 'drb-files-qa'

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
        self.createS3Client()

    def runProcess(self):
        if self.process == 'daily':
            startTimeStamp = datetime.now(timezone.utc) - timedelta(days=1)
            self.updateManifest(startTimeStamp)
        elif self.process == 'complete':
            self.updateManifest()
        elif self.process == 'custom':
            timeStamp = self.ingestPeriod
            startTimeStamp = datetime.strptime(timeStamp, '%Y-%m-%dT%H:%M:%S')
            self.updateManifest(startTimeStamp)

    def updateManifest(self, startTimeStamp=None):

        '''Load batch of LA works from past 24 hours'''

        batches = self.load_batch()
        for batch in batches:
            for c in batch['Contents']:
                if c["LastModified"] > startTimeStamp.replace(tzinfo=timezone.utc):
                    currKey = c['Key']
                    metadataObject = self.getObjectFromBucket(currKey, self.s3Bucket)
                    self.update_batch(metadataObject, self.s3Bucket, currKey)

    def update_batch(self, metadataObject, bucketName, currKey):
        dbManager = DBManager(
        user=os.environ.get('POSTGRES_USER', None),
        pswd=os.environ.get('POSTGRES_PSWD', None),
        host=os.environ.get('POSTGRES_HOST', None),
        port=os.environ.get('POSTGRES_PORT', None),
        db=os.environ.get('POSTGRES_NAME', None)
    )

        dbManager.generateEngine()

        dbManager.createSession()

        metadataJSON = json.loads(metadataObject['Body'].read().decode("utf-8"))
        metadataJSONCopy = copy.deepcopy(metadataJSON)
        
        metadataJSON = self.linkFulfill(metadataJSON, dbManager)
        metadataJSON = self.readingOrderFulfill(metadataJSON, dbManager)
        metadataJSON = self.resourceFulfill(metadataJSON, dbManager)
        metadataJSON = self.tocFulfill(metadataJSON, dbManager)

        if metadataJSON != metadataJSONCopy:
            try:
                fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False)
                return self.putObjectInBucket(
                    fulfillManifest, currKey, bucketName
                )
            except ClientError as e:
                logging.error(e)

    def linkFulfill(self, metadataJSON, dbManager):
        for i in metadataJSON['links']:
            i['href'] = self.fulfillReplace(i, dbManager)

        return metadataJSON
            
    def readingOrderFulfill(self, metadataJSON, dbManager):
        for i in metadataJSON['readingOrder']:
            i['href'] = self.fulfillReplace(i, dbManager)

        return metadataJSON

    def resourceFulfill(self, metadataJSON, dbManager):
        for i in metadataJSON['resources']:
            i['href'] = self.fulfillReplace(i, dbManager)

        return metadataJSON

    def tocFulfill(self, metadataJSON, dbManager): 
        for i in metadataJSON['toc']:
            if 'pdf' in i['href'] \
                or 'epub' in i['href']:
                    for link in dbManager.session.query(Link) \
                        .filter(Link.url == i['href'].replace('https://', '')):
                            i['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                            link.flags['fulfill_limited_access'] = True
        return metadataJSON

    @staticmethod
    def fulfillReplace(metadata, dbManager):
        if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
            or metadata['type'] == 'application/epub+xml':
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):
                        metadata['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                        link.flags['fulfill_limited_access'] = True
        return metadata['href']

    def load_batch(self):

        '''# Loading batches of JSON records using a paginator until there are no more batches'''

        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket= bucketName, Prefix= 'manifests/UofM/')
        return page_iterator

class FulfillError(Exception):
    pass