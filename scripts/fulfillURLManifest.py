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

    counter = 0
    
    metadataJSON, counter = linkFulfill(metadataJSON, counter, dbManager)
    metadataJSON, counter = readingOrderFulfill(metadataJSON, counter, dbManager)
    metadataJSON, counter = resourceFulfill(metadataJSON, counter, dbManager)
    metadataJSON, counter = tocFulfill(metadataJSON, counter, dbManager)

    if counter >= 4: 
        for link in metadataJSON['links']:
            fulfillFlagUpdate(link, dbManager)

    dbManager.closeConnection()

    if metadataJSON != metadataJSONCopy:
        try:
            fulfillManifest = json.dumps(metadataJSON, ensure_ascii = False)
            return s3_client.put_object(Bucket=bucketName, Key=currKey, \
                                Body=fulfillManifest, ACL= 'public-read', \
                                ContentType = 'application/json'
                )
        except ClientError as e:
            logging.error(e)

def linkFulfill(metadataJSON, counter, dbManager):
    for link in metadataJSON['links']:
        fulfillLink, counter = fulfillReplace(link, counter, dbManager)
        link['href'] = fulfillLink

    return (metadataJSON, counter)
        
def readingOrderFulfill(metadataJSON, counter, dbManager):
    for readOrder in metadataJSON['readingOrder']:
        fulfillLink, counter = fulfillReplace(readOrder, counter, dbManager)
        readOrder['href'] = fulfillLink

    return (metadataJSON, counter)

def resourceFulfill(metadataJSON, counter, dbManager):
    for resource in metadataJSON['resources']:
        fulfillLink, counter = fulfillReplace(resource, counter, dbManager)
        resource['href'] = fulfillLink

    return (metadataJSON, counter)

def tocFulfill(metadataJSON, counter, dbManager): 

    '''
    The toc dictionary has no "type" key like the previous dictionaries 
    therefore the 'href' key is evaluated instead
    '''
    
    for toc in metadataJSON['toc']:
        if 'pdf' in toc['href'] \
            or 'epub' in toc['href']:
                for link in dbManager.session.query(Link) \
                    .filter(Link.url == toc['href'].replace('https://', '')):
                        counter += 1
                        toc['href'] = f'http://{host}:{port}/fulfill/{link.id}'

    return (metadataJSON, counter)

def fulfillReplace(metadata, counter, dbManager):

    if metadata['type'] == 'application/pdf' or metadata['type'] == 'application/epub+zip' \
        or metadata['type'] == 'application/epub+xml':
            for link in dbManager.session.query(Link) \
                .filter(Link.url == metadata['href'].replace('https://', '')):          
                    counter += 1            
                    metadata['href'] = f'http://{host}:{port}/fulfill/{link.id}'

    return (metadata['href'], counter)

def fulfillFlagUpdate(metadata, dbManager):
    if metadata['type'] == 'application/webpub+json':
        for link in dbManager.session.query(Link) \
            .filter(Link.url == metadata['href'].replace('https://', '')):   
                    print(link)
                    print(link.flags)
                    if 'fulfill_limited_access' in link.flags.keys():
                        if link.flags['fulfill_limited_access'] == False:
                            newLinkFlag = dict(link.flags)
                            newLinkFlag['fulfill_limited_access'] = True
                            link.flags = newLinkFlag
                            dbManager.commitChanges()

def load_batches():

    '''# Loading batches of JSON records using a paginator until there are no more batches'''

    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket= bucketName, Prefix= 'manifests/UofM/')
    return page_iterator

if __name__ == '__main__':
    main()