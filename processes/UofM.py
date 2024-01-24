import json
import os
from requests.exceptions import HTTPError, ConnectionError
from botocore.exceptions import ClientError

from .core import CoreProcess
from urllib.error import HTTPError
from mappings.core import MappingError
from mappings.UofM import UofMMapping
from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)

class UofMProcess(CoreProcess):

    def __init__(self, *args):
        super(UofMProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete' 

        # Connect to database
        self.generateEngine()
        self.createSession()

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def runProcess(self):
        with open('UofM_CSV.json') as f:
                UofMData = json.load(f)

        for i in range(0, 12):
            metaDict = UofMData['data'][i]
            self.processUofMRecord(metaDict)

        self.saveRecords()
        self.commitChanges()

    def processUofMRecord(self, record):
        try:
            UofMRec = UofMMapping(record)
            UofMRec.applyMapping()
            self.addHasPartMapping(record, UofMRec.record)
            self.storePDFManifest(UofMRec.record)
            self.addDCDWToUpdateList(UofMRec)
            
        except (MappingError, HTTPError, ConnectionError, IndexError, TypeError) as e:
            logger.exception(e)
            logger.warn(UofMError('Unable to process UofM record'))

    def addHasPartMapping(self, resultsRecord, record):
        bucket = 'ump-pdf-repository'

        try:
            #The get_object method is to make sure the object with a specific bucket and key exists in S3
            self.s3Client.get_object(Bucket=bucket, 
                                    Key=f'{resultsRecord["File ID 1"]}_060pct.pdf')
            key = f'{resultsRecord["File ID 1"]}_060pct.pdf'
            urlPDFObject = f'https://{bucket}.s3.amazonaws.com/{key}'

            linkString = '|'.join([
                '1',
                urlPDFObject,
                'UofM',
                'application/pdf',
                '{"catalog": false, "download": true, "reader": false, "embed": false}'
            ])
            record.has_part.append(linkString)

        except ClientError or Exception or HTTPError as err:
            if err.response['Error']['Code'] == 'NoSuchKey':
                logger.info(UofMError("Key doesn't exist"))
            else: 
                logger.info(UofMError("Object doesn't exist"))

        if not record.has_part:
            try:
                #The get_object method is to make sure the object with a specific bucket and key exists in S3
                self.s3Client.get_object(Bucket= 'ump-pdf-repository', 
                                        Key= f'{resultsRecord["File ID 1"]}_100pct.pdf')
                key = f'{resultsRecord["File ID 1"]}_100pct.pdf'
                urlPDFObject = f'https://{bucket}.s3.amazonaws.com/{key}'

                linkString = '|'.join([
                    '1',
                    urlPDFObject,
                    'UofM',
                    'application/pdf',
                    '{"catalog": false, "download": true, "reader": false, "embed": false}'
                ])
                record.has_part.append(linkString)

            except ClientError or Exception or HTTPError as err:
                if err.response['Error']['Code'] == 'NoSuchKey':
                    logger.info(UofMError("Key doesn't exist"))
                else: 
                    logger.info(UofMError("Object doesn't exist"))
        

            
    def storePDFManifest(self, record):
        for link in record.has_part:
            itemNo, uri, source, mediaType, flags = link.split('|')

            if mediaType == 'application/pdf':
                logger.warn(f'Identifiers: {record.identifiers}')
                recordID = record.identifiers[0].split('|')[0]

                manifestPath = 'manifests/{}/{}.json'.format(source, recordID)
                manifestURI = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3Bucket, manifestPath
                )

                manifestJSON = self.generateManifest(record, uri, manifestURI)

                self.createManifestInS3(manifestPath, manifestJSON)

                linkString = '|'.join([
                    itemNo,
                    manifestURI,
                    source,
                    'application/webpub+json',
                    '{"catalog": false, "download": false, "reader": true, "embed": false}'
                ])

                record.has_part.insert(0, linkString)
                break

    def createManifestInS3(self, manifestPath, manifestJSON):
        self.putObjectInBucket(
            manifestJSON.encode('utf-8'), manifestPath, self.s3Bucket
        )

    @staticmethod
    def generateManifest(record, sourceURI, manifestURI):
        manifest = WebpubManifest(sourceURI, 'application/pdf')

        manifest.addMetadata(
            record,
            conformsTo=os.environ['WEBPUB_PDF_PROFILE']
        )
        
        manifest.addChapter(sourceURI, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifestURI,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()


class UofMError(Exception):
    pass
