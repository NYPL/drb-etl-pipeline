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

class Fulfill_Process(CoreProcess):

    def __init__(self, *args):
        super(Fulfill_Process, self).__init__(*args[:4])

        self.fullImport = self.process == 'complete' 
        self.startTimestamp = None

        # Connect to database
        self.generateEngine()
        self.createSession()

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']
        self.host = os.environ['DRB_API_HOST']
        self.prefix = 'manifests/UofM/'
        self.createS3Client()

    def runProcess(self):
        if self.process == 'daily':
            startTimeStamp = datetime.now(timezone.utc) - timedelta(days=1)
            self.get_manifests(startTimeStamp)
        elif self.process == 'complete':
            self.get_manifests()
        elif self.process == 'custom':
            time_stamp = self.ingestPeriod
            startTimeStamp = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S')
            self.get_manifests(startTimeStamp)

    def get_manifests(self, startTimeStamp=None):

        '''Load batch of LA works based on startTimeStamp'''

        batches = self.load_batches(self.prefix, self.s3Bucket)
        if startTimeStamp:
            #Using JMESPath to extract keys from the JSON batches
            filtered_batch_keys = batches.search(f"Contents[?to_string(LastModified) > '\"{startTimeStamp}\"'].Key")
            for key in filtered_batch_keys:
                metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key= f'{key}')
                self.update_manifest(metadata_object, self.s3Bucket, key)
        else:
            for batch in batches:
                for content in batch['Contents']:
                    key = content['Key']
                    metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key= f'{key}')
                    self.update_manifest(metadata_object, self.s3Bucket, key)

    def update_manifest(self, metadata_object, bucket_name, curr_key):

        metadata_json = json.loads(metadata_object['Body'].read().decode("utf-8"))
        metadata_json_copy = copy.deepcopy(metadata_json)

        rights_status = 'in copyright'
        rights_status = self.check_rights_status(metadata_json, rights_status)

        if rights_status != 'in copyright':
            return
        
        counter = 0
    
        metadata_json, counter = self.link_fulfill(metadata_json, counter)
        metadata_json, counter = self.reading_order_fulfill(metadata_json, counter)
        metadata_json, counter = self.resource_fulfill(metadata_json, counter)
        metadata_json, counter = self.toc_fulfill(metadata_json, counter)

        if counter >= 4: 
            for link in metadata_json['links']:
                self.fulfill_flag_update(link)

        self.closeConnection()

        if metadata_json != metadata_json_copy:
            try:
                fulfill_manifest = json.dumps(metadata_json, ensure_ascii = False)
                return self.s3Client.put_object(
                    Bucket=bucket_name, 
                    Key=curr_key, 
                    Body=fulfill_manifest, ACL= 'public-read', 
                    ContentType = 'application/json'
                )
            except ClientError as e:
                logging.error(e)

    def link_fulfill(self, metadata_json, counter):
        for link in metadata_json['links']:
            fulfill_link, counter = self.fulfill_replace(link, counter)
            link['href'] = fulfill_link

        return (metadata_json, counter)
            
    def reading_order_fulfill(self, metadata_json, counter):
        for read_order in metadata_json['readingOrder']:
            fulfill_link, counter = self.fulfill_replace(read_order, counter)
            read_order['href'] = fulfill_link

        return (metadata_json, counter)

    def resource_fulfill(self, metadata_json, counter):
        for resource in metadata_json['resources']:
            fulfill_link, counter = self.fulfill_replace(resource, counter)
            resource['href'] = fulfill_link

        return (metadata_json, counter)

    def toc_fulfill(self, metadata_json, counter): 

        '''
        The toc dictionary has no "type" key like the previous dictionaries 
        therefore the 'href' key is evaluated instead
        '''

        for toc in metadata_json['toc']:
            if 'pdf' in toc['href'] \
                or 'epub' in toc['href']:
                    for link in self.session.query(Link) \
                        .filter(Link.url == toc['href'].replace('https://', '')):
                            counter += 1
                            toc['href'] = f'https://{self.host}/fulfill/{link.id}'

        return (metadata_json, counter)

    def fulfill_replace(self, metadata, counter):
        if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
            or metadata['type'] == 'application/epub+xml':
                for link in self.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):
                            counter += 1            
                            metadata['href'] = f'https://{self.host}/fulfill/{link.id}'

        return (metadata['href'], counter)
    
    def fulfill_flag_update(self, metadata):
        if metadata['type'] == 'application/webpub+json':
            for link in self.session.query(Link) \
                .filter(Link.url == metadata['href'].replace('https://', '')):   
                        if 'fulfill_limited_access' in link.flags.keys():
                            if link.flags['fulfill_limited_access'] == False:
                                newLinkFlag = dict(link.flags)
                                newLinkFlag['fulfill_limited_access'] = True
                                link.flags = newLinkFlag
                                self.commitChanges()
                        
    def check_rights_status(self, metadata_json, rights_status):
        for metadata in metadata_json['links']:
            if metadata['type'] == 'application/webpub+json':
                for link in self.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):   
                        if 'fulfill_limited_access' not in link.flags.keys():
                            rights_status = 'public domain'
                        return rights_status

class FulfillError(Exception):
    pass
