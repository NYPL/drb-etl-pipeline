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
        if self.process == 'daily':
            start_timestamp = datetime.now(timezone.utc) - timedelta(days=1)
            self.fetch_and_update_manifests(start_timestamp)
        elif self.process == 'complete':
            start_timestamp = None
            self.fetch_and_update_manifests(start_timestamp)
        elif self.process == 'custom':
            time_stamp = self.ingestPeriod
            start_timestamp = datetime.strptime(time_stamp, '%Y-%m-%dT%H:%M:%S')
            self.fetch_and_update_manifests(start_timestamp)

    def fetch_and_update_manifests(self, start_timestamp=None):

        batches = self.load_batches(self.prefix, self.s3Bucket)
        if start_timestamp:
            #Using JMESPath to extract keys from the JSON batches
            filtered_batch_keys = batches.search(f"Contents[?to_string(LastModified) > '\"{start_timestamp}\"'].Key")
            for key in filtered_batch_keys:
                metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key= f'{key}')
                self.update_metadata_object(metadata_object, self.s3Bucket, key)
        else:
            for batch in batches:
                for content in batch['Contents']:
                    key = content['Key']
                    metadata_object = self.s3Client.get_object(Bucket=self.s3Bucket, Key= f'{key}')
                    self.update_metadata_object(metadata_object, self.s3Bucket, key)

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
        except (Exception, IndexError) as e:
            logger.error(e)
        except:
            logger.error('One of the Link fulfill methods failed')  

        if counter >= 4: 
            for link in metadata_json['links']:
                self.fulfill_flag_update(link)

        self.closeConnection()

        self.replace_manifest_object(metadata_json, metadata_json_copy, bucket_name, curr_key)

    def replace_manifest_object(self, metadata_json, metadata_json_copy, bucket_name, curr_key):
        if metadata_json != metadata_json_copy:
            try:
                fulfill_manifest = json.dumps(metadata_json, ensure_ascii = False)
                return self.s3Client.put_object(
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
                        
    def check_copyright_status(self, metadata_json):
        for link in metadata_json['links']:
            if link['type'] == 'application/webpub+json':
                for psql_link in self.session.query(Link) \
                    .filter(Link.url == link['href'].replace('https://', '')):   
                        if 'fulfill_limited_access' not in psql_link.flags.keys():
                            copyright_status = False
                        else:
                            copyright_status = True

                        return copyright_status

class FulfillError(Exception):
    pass
