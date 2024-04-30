import boto3
import json
import os
import logging
from botocore.exceptions import ClientError
from model import Link
from managers import DBManager, s3

s3_client = boto3.client("s3")

bucketName = 'drb-files-qa'

# class fulfillURLManifest():

#     def __init__(self):

#         # Connect to database
#         self.generateEngine()
#         self.createSession()

#         # S3 Configuration
#         self.s3Bucket = bucketName
#         self.createS3Client()

def main():

    '''Replacing pdf/epub links in with fulfill urls in manifest JSON files'''

    batches = load_batch()
    for batch in batches:
        for c in batch['Contents']:
            currKey = c['Key']
            metadataObject = s3_client.get_object(Bucket= bucketName, Key= f'{currKey}')
            update_batch(metadataObject, bucketName, currKey)
    

def update_batch(metadataObject, bucketName, currKey):

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
    
    metadataJSON = linkFulfill(metadataJSON, dbManager)
    metadataJSON = readingOrderFulfill(metadataJSON, dbManager)
    metadataJSON = resourceFulfill(metadataJSON, dbManager)
    metadataJSON = tocFulfill(metadataJSON, dbManager)

    fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False, indent = 6)

    try:
        return s3_client.put_object(Bucket=bucketName, Key='manifests/UofM/0472030132.json', \
                            Body=fulfillManifest, ACL= 'public-read', \
                            ContentType = 'application/json'
            )
    except ClientError as e:
        logging.error(e)

def linkFulfill(metadataJSON, dbManager):
    for i in metadataJSON['links']:
        if i['type'] == 'application/pdf' or i['type'] == 'application/epub+zip' \
            or i['type'] == 'application/epub+xml':
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == i['href'].replace('https://', '')):
                        i['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                        return metadataJSON
                
def readingOrderFulfill(metadataJSON, dbManager):
    for i in metadataJSON['readingOrder']:
        if i['type'] == 'application/pdf' or i['type'] == 'application/epub+zip' \
            or i['type'] == 'application/epub+xml':
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == i['href'].replace('https://', '')):
                        i['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                        return metadataJSON

def resourceFulfill(metadataJSON, dbManager):
    for i in metadataJSON['resources']:
        if i['type'] == 'application/pdf' or i['type'] == 'application/epub+zip' \
            or i['type'] == 'application/epub+xml':
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == i['href'].replace('https://', '')):
                        i['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                        return metadataJSON

def tocFulfill(metadataJSON, dbManager): 
    for i in metadataJSON['toc']:
        if 'pdf' in i['href'] \
            or 'epub' in i['href']:
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == i['href'].replace('https://', '')):
                        i['href'] = f'http://127.0.0.1:5050/fulfill/{link.id}'
                        return metadataJSON

def load_batch():

    '''# Loading batches of JSON records using a paginator until there are no more batches'''

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket= bucketName, Prefix= 'manifests/UofM/')
    return page_iterator