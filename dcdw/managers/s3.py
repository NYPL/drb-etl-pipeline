import hashlib
import boto3
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
        if not 'Location' in s3Resp:
            return True

        raise Exception('Unable to create bucket in s3')
    
    def putObjectInBucket(self, obj, objKey, bucket, bucketPermissions='public-read'):
        objMD5 = S3Manager.getmd5HashOfObject(obj)
        try: 
            existingObj = self.getObjectFromBucket(objKey, bucket, md5Hash=objMD5)
            s3Resp = self.s3Client.put_object(
                ACL=bucketPermissions,
                Body=obj,
                Bucket=bucket,
                Key=objKey
            )

            if 'ETag' in s3Resp:
                return True
        except Exception as err:
            pass
        
        raise Exception('Unable to store file in s3')

    def getObjectFromBucket(self, objKey, bucket, md5Hash=None):
        s3Resp = self.s3Client.get_object(
            Bucket=bucket,
            Key=objKey,
            IfNoneMatch=md5Hash
        )

        if s3Resp.statusCode == 304:
            raise Exception('File exists in unmodified form')

        if 'Body' in s3Resp:
            return s3Resp
        
        raise Exception('Unable to get object from s3')

    @staticmethod
    def getmd5HashOfObject(obj):
        m = hashlib.md5()
        m.update(obj)
        return m.hexdigest()
