import os
import boto3
import re
import numpy 

from model import Edition, Item, Link
from model.postgres.item import ITEM_LINKS
from managers import DBManager

s3_client = boto3.client("s3")

bucketName = 'ump-pdf-repository-logs'

def main():
    
    
    '''
    The edition title, identifier, and timestamp are parsed out of the 
    S3 server access log files for UMP download requests
    '''

    requestRegex = r'REST.GET.OBJECT '
    fileIDRegex = r'REST.GET.OBJECT (.+pdf\s)' #File ID includes the file name for the pdf object
    timeStampRegex = r'\[.+\]'
    referrerRegex = r'https://drb-qa.nypl.org/'
    umpDownloadArray = [['title', 'timeStamp', 'identifier']]

    batches = load_batch()
    for batch in batches:
        for c in batch['Contents']:
            currKey = str(c['Key'])
            #logObject is a dict type
            logObject = s3_client.get_object(Bucket= bucketName, Key= f'{currKey}')
            for i in logObject['Body'].iter_lines():
                logObject = i.decode('utf8')
                parseTuple = parseInfo(logObject, requestRegex, referrerRegex, timeStampRegex, fileIDRegex)
                if parseTuple:
                    umpDownloadArray.append(parseTuple)
    umpDownloadCSV = numpy.array(umpDownloadArray)
    with open('data3.csv', 'w') as f: 
        f.write(str(umpDownloadCSV))

def load_batch():
    paginator = s3_client.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket= bucketName, Prefix= 'logs/946183545209/us-east-1/ump-pdf-repository/2024/03/13/')
    return page_iterator

def parseInfo(logObject, requestRegex, referrerRegex, timeStampRegex, fileIDRegex):
    matchRequest = re.search(requestRegex, logObject)
    matchReferrer = re.search(referrerRegex, logObject) 
    
    if matchRequest and matchReferrer and '403 AccessDenied' not in logObject:
        matchTime = re.search(timeStampRegex, logObject)
        matchFileID = re.search(fileIDRegex, logObject)
        linkGroup = matchFileID.group(1)
        titleParse = ''
        idParse = None

        dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )
        dbManager.generateEngine()

        dbManager.createSession()

        for item in dbManager.session.query(Item) \
            .filter(Item.source == 'UofM'):
            for link in dbManager.session.query(Link) \
                .join(ITEM_LINKS) \
                .filter(ITEM_LINKS.c.item_id == item.id) \
                .filter(Link.media_type == 'application/pdf') \
                .filter(Link.url.contains(linkGroup.strip())).all(): 
                    itemEditID = item.edition_id
                    for edit in dbManager.session.query(Edition) \
                        .filter(Edition.id == itemEditID):
                            titleParse = edit.title
                            idParse = edit.id
        
        dbManager.closeConnection()

        return [titleParse, matchTime.group(0), idParse]


if __name__ == '__main__':
    main()