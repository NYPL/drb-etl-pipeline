import boto3
from botocore.exceptions import ClientError
import hashlib
import os


class S3Manager:
    def __init__(self):
        pass

    def createS3Client(self):
        self.s3Client = boto3.client(
            's3',
            aws_access_key=os.environ['AWS_ACCESS'],
            aws_secret_access_key=os.environ['AWS_SECRET'],
            region=os.environ['AWS_REGION']
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

        existingObject = self.getObjectFromBucket(objKey, bucket, md5Hash=objMD5)
        if not existingObject or existingObject.statusCode != 304:
            try:
                return self.s3Client.put_object(
                    ACL=bucketPermissions,
                    Body=obj,
                    Bucket=bucket,
                    Key=objKey
                )
            except ClientError as e:
                print(e)
                raise S3Error('UNable to store file in s3')
        
        return None

    def getObjectFromBucket(self, objKey, bucket, md5Hash=None):
        try:
            return self.s3Client.get_object(
                Bucket=bucket,
                Key=objKey,
                IfNoneMatch=md5Hash
            )
        except ClientError as e:
            print(e)
            raise S3Error('Unable to get object from s3')

    @staticmethod
    def getmd5HashOfObject(obj):
        m = hashlib.md5()
        m.update(obj)
        return m.hexdigest()


class S3Error(Exception):
    def __init__(self, message=None):
        self.message = message
