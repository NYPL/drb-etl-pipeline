import boto3
import json
import os
import logging
import os 

import copy 
from botocore.exceptions import ClientError
from model import Link
from managers import DBManager

s3_client = boto3.client("s3")

bucketName = 'drb-files-qa'

host = os.environ['DRB_API_HOST']
port = os.environ['DRB_API_PORT']

def main():

    '''Replacing pdf/epub links in with fulfill urls in manifest JSON files'''

    batches = load_batches()
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
    metadataJSONCopy = copy.deepcopy(metadataJSON)
    
    metadataJSON = linkFulfill(metadataJSON, dbManager)
    metadataJSON = readingOrderFulfill(metadataJSON, dbManager)
    metadataJSON = resourceFulfill(metadataJSON, dbManager)
    metadataJSON = tocFulfill(metadataJSON, dbManager)

    if metadataJSON != metadataJSONCopy:
        try:
            fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False)
            return s3_client.put_object(Bucket=bucketName, Key=currKey, \
                                Body=fulfillManifest, ACL= 'public-read', \
                                ContentType = 'application/json'
                )
        except ClientError as e:
            logging.error(e)

def linkFulfill(metadataJSON, dbManager):
    for i in metadataJSON['links']:
        i['href'] = fulfillReplace(i, dbManager)

    return metadataJSON
        
def readingOrderFulfill(metadataJSON, dbManager):
    for i in metadataJSON['readingOrder']:
        i['href'] = fulfillReplace(i, dbManager)

    return metadataJSON

def resourceFulfill(metadataJSON, dbManager):
    for i in metadataJSON['resources']:
        i['href'] = fulfillReplace(i, dbManager)

    return metadataJSON

def tocFulfill(metadataJSON, dbManager): 
    for i in metadataJSON['toc']:
        if 'pdf' in i['href'] \
            or 'epub' in i['href']:
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == i['href'].replace('https://', '')):
                        i['href'] = f'http://{host}:{port}/fulfill/{link.id}'
    return metadataJSON

def fulfillReplace(metadata, dbManager):
    if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
        or metadata['type'] == 'application/epub+xml':
            for link in dbManager.session.query(Link) \
                .filter(Link.url == metadata['href'].replace('https://', '')):
                    metadata['href'] = f'http://{host}:{port}/fulfill/{link.id}'
    return metadata['href']

def load_batches():

    '''# Loading batches of JSON records using a paginator until there are no more batches'''

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket= bucketName, Prefix= 'manifests/UofM/')
    return page_iterator

if __name__ == '__main__':
    main()