import json
import os
import copy
from botocore.exceptions import ClientError
from typing import Optional

from datetime import datetime
from managers import DBManager, S3Manager
from model import Link
from logger import create_log
from .. import utils

logger = create_log(__name__)

class FulfillURLManifestProcess():

    def __init__(self, *args):
        self.process = args[0]
        self.ingest_period = args[2]

        self.db_manager = DBManager() 
        self.db_manager.createSession()

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.host = os.environ['DRB_API_HOST']
        self.prefix = 'manifests/publisher_backlist/'
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):
        start_timestamp = utils.get_start_datetime(process_type=self.process, ingest_period=self.ingest_period)

        self.fetch_and_update_manifests(start_timestamp=start_timestamp)

    def fetch_and_update_manifests(self, start_timestamp: Optional[datetime]=None):

        batches = self.s3_manager.load_batches(self.prefix, self.s3_bucket)
        if start_timestamp:
            #Using JMESPath to extract keys from the JSON batches
            filtered_batch_keys = batches.search(f"Contents[?to_string(LastModified) > '\"{start_timestamp}\"'].Key")
            for key in filtered_batch_keys:
                if not key:
                    continue

                metadata_object = self.s3_manager.s3Client.get_object(Bucket=self.s3_bucket, Key=f'{key}')
                self.update_metadata_object(metadata_object, self.s3_bucket, key)
        else:
            for batch in batches:
                if 'Contents' not in batch:
                    continue

                for content in batch['Contents']:
                    key = content['Key']
                    metadata_object = self.s3_manager.s3Client.get_object(Bucket=self.s3_bucket, Key=f'{key}')
                    self.update_metadata_object(metadata_object, self.s3_bucket, key)

    def update_metadata_object(self, metadata_object, bucket_name, curr_key):

        metadata_json = json.loads(metadata_object['Body'].read().decode("utf-8"))
        metadata_json_copy = copy.deepcopy(metadata_json)

        copyright_status = self.check_copyright_status(metadata_json)

        if copyright_status == False:
            return
        
        counter = 0
    
        try:
            metadata_json, counter = self.link_fulfill(metadata_json, counter)
            metadata_json, counter = self.reading_order_fulfill(metadata_json, counter)
            metadata_json, counter = self.resource_fulfill(metadata_json, counter)
            metadata_json, counter = self.toc_fulfill(metadata_json, counter)
        except Exception as e:
            logger.exception(e)

        if counter >= 4: 
            for link in metadata_json['links']:
                self.fulfill_flag_update(link)

        self.db_manager.closeConnection()

        self.replace_manifest_object(metadata_json, metadata_json_copy, bucket_name, curr_key)

    def replace_manifest_object(self, metadata_json, metadata_json_copy, bucket_name, curr_key):
        if metadata_json != metadata_json_copy:
            try:
                fulfill_manifest = json.dumps(metadata_json, ensure_ascii = False)
                return self.s3_manager.s3Client.put_object(
                    Bucket=bucket_name, 
                    Key=curr_key, 
                    Body=fulfill_manifest, 
                    ACL= 'public-read', 
                    ContentType = 'application/json'
                )
            except ClientError as e:
                logger.error(e)

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
                    for link in self.db_manager.session.query(Link) \
                        .filter(Link.url == toc['href'].replace('https://', '')):
                            counter += 1
                            toc['href'] = f'https://{self.host}/fulfill/{link.id}'

        return (metadata_json, counter)

    def fulfill_replace(self, metadata, counter):
        if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
            or metadata['type'] == 'application/epub+xml':
                for link in self.db_manager.session.query(Link) \
                    .filter(Link.url == metadata['href'].replace('https://', '')):
                            counter += 1            
                            metadata['href'] = f'https://{self.host}/fulfill/{link.id}'

        return (metadata['href'], counter)
    
    def fulfill_flag_update(self, metadata):
        if metadata['type'] == 'application/webpub+json':
            for link in self.db_manager.session.query(Link) \
                .filter(Link.url == metadata['href'].replace('https://', '')):   
                        if 'fulfill_limited_access' in link.flags.keys():
                            if link.flags['fulfill_limited_access'] == False:
                                newLinkFlag = dict(link.flags)
                                newLinkFlag['fulfill_limited_access'] = True
                                link.flags = newLinkFlag
                                self.db_manager.commitChanges()
                        
    def check_copyright_status(self, metadata_json):
        for link in metadata_json['links']:
            if link['type'] == 'application/webpub+json':
                for psql_link in self.db_manager.session.query(Link) \
                    .filter(Link.url == link['href'].replace('https://', '')):   
                        if 'fulfill_limited_access' not in psql_link.flags.keys():
                            copyright_status = False
                        else:
                            copyright_status = True

                        return copyright_status

class FulfillError(Exception):
    pass
