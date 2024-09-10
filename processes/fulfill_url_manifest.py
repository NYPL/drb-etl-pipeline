import json
import os
import copy
from botocore.exceptions import ClientError

from .core import CoreProcess
from datetime import datetime, timedelta, timezone
from model import Link
from logger import createLog

logger = createLog(__name__)

class FulfillURLManifestProcess(CoreProcess):
    def __init__(self, *args):
        super(FulfillURLManifestProcess, self).__init__(*args[:4])

        self.fullImport = self.process == 'complete' 
        self.start_timestamp = None

        self.generateEngine()
        self.createSession()

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.host = os.environ['DRB_API_HOST']
        self.prefix = 'manifests/UofM/'
        self.createS3Client()

    def runProcess(self):
        try:
            if self.process == 'daily':
                start_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
                self.update_manifests(start_timestamp)
            elif self.process == 'complete':
                start_timestamp = None
                self.update_manifests(start_timestamp)
            elif self.process == 'custom':
                time_stamp = self.ingestPeriod
                start_timestamp = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S')
                self.update_manifests(start_timestamp)
        finally:
            self.closeConnection()

    def update_manifests(self, start_timestamp=None):
        batches = self.load_batches(self.prefix, self.s3Bucket)
        
        if start_timestamp:
            #Using JMESPath to extract keys from the JSON batches
            filtered_batch_keys = batches.search(f"Contents[?to_string(LastModified) > '\"{start_timestamp}\"'].Key")
            for key in filtered_batch_keys:
                metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key=key)
                self.update_manifest_with_fulfill_links(metadata_object, self.s3Bucket, key)
        else:
            for batch in batches:
                for content in batch['Contents']:
                    key = content['Key']
                    metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key=key)
                    self.update_manifest_with_fulfill_links(metadata_object, self.s3Bucket, key)

    def update_manifest_with_fulfill_links(self, metadata_object, bucket_name, key):
        manifest_to_update = json.loads(metadata_object['Body'].read().decode("utf-8"))
        original_manifest = copy.deepcopy(manifest_to_update)

        if not self.is_limited_access(manifest_to_update):
            return
            
        manifest_to_update['links'] = map(lambda link: self.update_with_fulfill_link(link), manifest_to_update['links'])
        manifest_to_update['readingOrder'] = map(lambda link: self.update_with_fulfill_link(link), manifest_to_update['readingOrder'])
        manifest_to_update['resources'] = map(lambda link: self.update_with_fulfill_link(link), manifest_to_update['resources'])
        manifest_to_update['toc'] = self.get_fulfill_toc_links(manifest_to_update)

        if manifest_to_update == original_manifest:
            return

        for link in manifest_to_update['links']:
            self.update_fulfill_flag(link)

        self.update_manifest_object(manifest_to_update, bucket_name, key)

    def update_manifest_object(self, manifest, bucket_name, key):
        try:
            return self.s3Client.put_object(
                Bucket=bucket_name, 
                Key=key, 
                Body=json.dumps(manifest, ensure_ascii=False), 
                ACL= 'public-read', 
                ContentType = 'application/json'
            )
        except ClientError as e:
            logger.error(e)

    def get_fulfill_toc_links(self, toc_links): 
        for toc in toc_links:
            if 'pdf' in toc['href'] or 'epub' in toc['href']:
                link_id = self.session.query(Link).filter(Link.url == toc['href'].replace('https://', '')).first().id
                toc['href'] = f'https://{self.host}/fulfill/{link_id}'

        return toc_links

    def update_with_fulfill_link(self, link):
        if link['type'] == 'application/pdf' or link['type'] == 'application/epub+zip' or link['type'] == 'application/epub+xml':
            link_id = self.session.query(Link).filter(Link.url == link['href'].replace('https://', '')).first().id
            link['href'] = f'https://{self.host}/fulfill/{link_id}'

        return link['href']
    
    def update_fulfill_flag(self, link):
        if link['type'] == 'application/webpub+json':
            for db_link in self.session.query(Link).filter(Link.url == link['href'].replace('https://', '')):   
                if 'fulfill_limited_access' in db_link.flags.keys():
                    if db_link.flags['fulfill_limited_access'] == False:
                        new_link_flag = dict(link.flags)
                        new_link_flag['fulfill_limited_access'] = True
                        link.flags = new_link_flag
                        self.commitChanges()
                        
    def is_limited_access(self, manifest):
        for link in manifest['links']:
            if link['type'] == 'application/webpub+json':
                for db_link in self.session.query(Link).filter(Link.url == link['href'].replace('https://', '')):
                    if 'fulfill_limited_access' in db_link.flags.keys():
                        return True
        
        return False

class FulfillError(Exception):
    pass
