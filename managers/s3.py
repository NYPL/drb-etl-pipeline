import base64
import boto3
from botocore.exceptions import ClientError
import hashlib
from io import BytesIO
import os
from zipfile import ZipFile


class S3Manager:
    def __init__(self):
        pass

    def createS3Client(self):
        self.s3Client = boto3.client(
            's3',
            aws_access_key_id=os.environ.get('AWS_ACCESS', None),
            aws_secret_access_key=os.environ.get('AWS_SECRET', None),
            region_name=os.environ.get('AWS_REGION', None)
        )
    
    def createS3Bucket(self, bucketName, bucketPermissions):
        s3Resp = self.s3Client.create_bucket(
            ACL=bucketPermissions,
            Bucket=bucketName
        )

        if 'Location' in s3Resp:
            return True

        raise S3Error('Unable to create bucket in s3')
    
    def putObjectInBucket(self, obj, objKey, bucket, bucketPermissions='public-read'):
        objMD5 = S3Manager.getmd5HashOfObject(obj)
        objExtension = objKey[-4:].lower()

        existingObject = None
        try:
            if objExtension == 'epub':
                existingObject = self.getObjectFromBucket(objKey, bucket, md5Hash=objMD5)
        except S3Error:
            print('{} does not yet exist'.format(objKey))

        if existingObject and\
            (existingObject['ResponseMetadata']['HTTPStatusCode'] == 304\
            or existingObject['Metadata'].get('md5checksum', None) == objMD5):
                print('Skipping existing, unmodified file {}'.format(objKey))
                return None

        try:
            if objExtension == 'epub':
                self.putExplodedEpubComponentsInBucket(obj, objKey, bucket)

            return self.s3Client.put_object(
                ACL=bucketPermissions,
                Body=obj,
                Bucket=bucket,
                Key=objKey,
                ContentMD5=objMD5,
                Metadata={'md5Checksum': objMD5}
            )
        except ClientError as e:
            raise S3Error('Unable to store file in s3')

    def putExplodedEpubComponentsInBucket(self, obj, objKey, bucket):
        keyRoot = objKey.split('.')[0] 

        with ZipFile(BytesIO(obj), 'r') as epubZip:
            for component in epubZip.namelist():
                componentObj = epubZip.open(component).read()
                componentKey = '{}/{}'.format(keyRoot, component)
                self.putObjectInBucket(componentObj, componentKey, bucket)

    def getObjectFromBucket(self, objKey, bucket, md5Hash=None):
        try:
            return self.s3Client.get_object(
                Bucket=bucket,
                Key=objKey,
                IfNoneMatch=md5Hash
            )
        except ClientError as e:
            raise S3Error('Unable to get object from s3')

    @staticmethod
    def getmd5HashOfObject(obj):
        m = hashlib.md5()
        m.update(obj)
        return base64.b64encode(m.digest()).decode('utf-8')


class S3Error(Exception):
    def __init__(self, message=None):
        self.message = message
