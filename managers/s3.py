import base64
import boto3
from botocore.exceptions import ClientError
import hashlib
import json
import dataclasses
from io import BytesIO
import mimetypes
import os
from zipfile import ZipFile
from managers import WebpubManifest
from digital_assets import get_stored_file_url
from model import Part, FileFlags\

from logger import create_log

logger = create_log(__name__)


class S3Manager:
    def __init__(self):
        pass

    def createS3Client(self):
        self.s3Client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS', None),
            aws_secret_access_key=os.environ.get('AWS_SECRET', None),
            region_name=os.environ.get('AWS_REGION', None),
            endpoint_url=os.environ.get('S3_ENDPOINT_URL', None)
        )

    def createS3Bucket(self, bucketName, bucketPermissions):
        s3Resp = self.s3Client.create_bucket(
            ACL=bucketPermissions,
            Bucket=bucketName
        )

        if 'Location' in s3Resp:
            return True

        raise S3Error('Unable to create bucket in s3')


    def store_pdf_manifest(self, record, bucket_name, requires_login: bool):
        for link in record.has_part:
            item_no, uri, source, media_type, _ = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]

                if requires_login:
                    manifest_path = f'manifests/publisher_backlist/{source}/{record_id}.json'
                else:
                    manifest_path = f'manifests/{source}/{record_id}.json''manifests/{}/{}.json'

                manifest_uri = get_stored_file_url(storage_name=bucket_name, file_path=manifest_path)

                manifest_json = self.generate_manifest(record, uri, manifest_uri)

                self.create_manifest_in_s3(manifest_path, manifest_json, bucket_name)

                if source == 'clacso':
                    link_string = Part(
                        index=item_no, 
                        url=manifest_uri,
                        source=source,
                        file_type='application/webpub+json',
                        flags=json.dumps(dataclasses.asdict(FileFlags()))
                    ).to_string()
                elif requires_login:
                    manifest_flags = {
                    'catalog': False,
                    'download': False,
                    'reader': True,
                    'embed': False,
                    **({'fulfill_limited_access': False} if requires_login else {})
                    }
                    link_string = Part(
                        index=item_no, 
                        url=manifest_uri,
                        source=source,
                        file_type='application/webpub+json',
                        flags=json.dumps(manifest_flags)
                    ).to_string()
                else:
                    link_string = Part(
                        index=item_no, 
                        url=manifest_uri,
                        source=source,
                        file_type='application/webpub+json',
                        flags=json.dumps(dataclasses.asdict(FileFlags(reader=True)))
                    ).to_string()

                record.has_part.insert(0, link_string)
                break

    def create_manifest_in_s3(self, manifestPath, manifestJSON, s3_bucket: str):
        self.putObjectInBucket(
            manifestJSON.encode('utf-8'), manifestPath, s3_bucket
        )

    def generate_manifest(self, record, source_url, manifest_url):
        manifest = WebpubManifest(source_url, 'application/pdf')

        manifest.addMetadata(record)
        
        manifest.addChapter(source_url, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_url,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()

    def putObjectInBucket(
        self, obj, objKey, bucket, bucketPermissions='public-read'
    ):
        objMD5 = S3Manager.getmd5HashOfObject(obj)
        objExtension = objKey[-4:].lower()

        existingObject = None
        try:
            if objExtension == 'epub':
                existingObject = self.getObjectFromBucket(
                    objKey, bucket, md5Hash=objMD5
                )
        except S3Error:
            logger.info('{} does not yet exist'.format(objKey))

        if existingObject and (
            existingObject['ResponseMetadata']['HTTPStatusCode'] == 304
            or existingObject['Metadata'].get('md5checksum', None) == objMD5
        ):
            logger.info('Skipping existing, unmodified file {}'.format(objKey))
            return None

        try:
            if objExtension == 'epub':
                self.putExplodedEpubComponentsInBucket(obj, objKey, bucket)

            objectType = mimetypes.guess_type(objKey)[0]\
                or 'binary/octet-stream'

            return self.s3Client.put_object(
                ACL=bucketPermissions,
                Body=obj,
                Bucket=bucket,
                Key=objKey,
                ContentMD5=objMD5,
                ContentType=objectType,
                Metadata={'md5Checksum': objMD5}
            )
        except ClientError as e:
            raise S3Error(f'Unable to store file {objKey} in s3: {e}')

    def putExplodedEpubComponentsInBucket(self, obj, objKey, bucket):
        keyRoot = '.'.join(objKey.split('.')[:-1])

        with ZipFile(BytesIO(obj), 'r') as epubZip:
            for component in epubZip.namelist():
                componentObj = epubZip.open(component).read()
                componentKey = '{}/{}'.format(keyRoot, component)
                self.putObjectInBucket(componentObj, componentKey, bucket)

    def getObjectFromBucket(self, objKey, bucket, md5Hash=None):
        try:
            if md5Hash:
                return self.s3Client.get_object(
                    Bucket=bucket,
                    Key=objKey,
                    IfNoneMatch=md5Hash
                )
            
            return self.s3Client.get_object(Bucket=bucket, Key=objKey)
        except ClientError:
            raise S3Error('Unable to get object from s3')
        
    def load_batches(self, objKey, bucket):

        '''# Loading batches of data using a paginator until there are no more batches'''

        paginator = self.s3Client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket, Prefix=objKey)
        return page_iterator

    @staticmethod
    def getmd5HashOfObject(obj):
        m = hashlib.md5()
        m.update(obj)
        return base64.b64encode(m.digest()).decode('utf-8')


class S3Error(Exception):
    def __init__(self, message=None):
        self.message = message
