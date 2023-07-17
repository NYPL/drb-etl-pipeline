import json
import os, requests
from requests.exceptions import HTTPError, ConnectionError

from .core import CoreProcess
from mappings.core import MappingError
from mappings.loc import LOCMapping
from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)

LOC_ROOT_OPEN_ACCESS = 'https://www.loc.gov/collections/open-access-books/?fo=json&fa=access-restricted%3Afalse&c=2&at=results'
LOC_ROOT_DIGIT = 'https://www.loc.gov/collections/selected-digitized-books/?fo=json&fa=access-restricted%3Afalse&c=2&at=results' 

class LOCProcess(CoreProcess):

    def __init__(self, *args):
        super(LOCProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete' 

        # Connect to database
        self.generateEngine()
        self.createSession()

        # Connect to epub processing queue
        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.fileQueue, self.fileRoute)

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def runProcess(self):
        openAccessRequestCount = 0 
        digitizedRequestCount = 0

        try:
            openAccessRequestCount = self.importOpenAccessRecords(openAccessRequestCount)

        except Exception or HTTPError as e:
            logger.exception(e)

        try:
            digitizedRequestCount = self.importDigitizedRecords(digitizedRequestCount)
        
        except Exception or HTTPError as e:
            logger.exception(e)

        self.saveRecords()
        self.commitChanges()

    def importOpenAccessRecords(self, count):
        sp = 2
        try:
            while sp > 0:
                openAccessURL = '{}&sp={}'.format(LOC_ROOT_OPEN_ACCESS, sp)
                jsonData = self.fetchPageJSON(openAccessURL)
                LOCData = jsonData.json()
                for metaDict in LOCData['results']:
                    resources = metaDict['resources'][0]
                    if 'pdf' in resources.keys() or 'epub_file' in resources.keys():
                        logger.debug(f'OPEN ACCESS URL: {openAccessURL}')
                        logger.debug(f"TITLE: {metaDict['title']}")
                        self.processLOCRecord(metaDict)
                        count += 1
                        logger.debug(f'Count for OP Access: {count}')
                sp += 1

        except Exception or HTTPError as e:
            if e == Exception:
                logger.exception(e)
            else:
                logger.debug('Open Access Collection Ingestion Complete')

        return count

    def importDigitizedRecords(self, count):
        sp = 2
        try:
            while sp > 0:
                digitizedURL = '{}&sp={}'.format(LOC_ROOT_DIGIT, sp)
                jsonData = self.fetchPageJSON(digitizedURL)
                LOCData = jsonData.json()
                for metaDict in LOCData['results']:
                    resources = metaDict['resources'][0]
                    if 'pdf' in resources.keys() or 'epub_file' in resources.keys():
                        logger.debug(f'DIGITIZED URL: {digitizedURL}')
                        logger.debug(f"TITLE: {metaDict['title']}")
                        self.processLOCRecord(metaDict)
                        count += 1
                        logger.debug(f'Count for Digitized: {count}')
                sp += 1
            return count
        
        except Exception or HTTPError as e:
            if e == Exception:
                logger.exception(e)
            else:
                logger.debug('Digitized Books Collection Ingestion Complete')

    def processLOCRecord(self, record):
        try:
            LOCRec = LOCMapping(record)
            LOCRec.applyMapping()
            self.addHasPartMapping(record, LOCRec.record)
            self.storePDFManifest(LOCRec.record)
            self.storeEpubsInS3(LOCRec.record)
            self.addDCDWToUpdateList(LOCRec)
            
        except (MappingError, HTTPError, ConnectionError, IndexError, TypeError) as e:
            logger.exception(e)
            logger.warn(LOCError('Unable to process LOC record'))
            
    def addHasPartMapping(self, resultsRecord, record):
        if 'pdf' in resultsRecord['resources'][0].keys():
            linkString = '|'.join([
                '1',
                resultsRecord['resources'][0]['pdf'],
                'loc',
                'application/pdf',
                '{"catalog": false, "download": true, "reader": false, "embed": false}'
            ])
            record.has_part.append(linkString)

        if 'epub_file' in resultsRecord['resources'][0].keys():
            linkString2 = '|'.join([
                '1',
                resultsRecord['resources'][0]['epub_file'],
                'loc',
                'application/epub+zip',
                '{"reader": false, "catalog": false, "download": true}'
            ])
            record.has_part.append(linkString2)


    def storePDFManifest(self, record):
        for link in record.has_part:
            itemNo, uri, source, mediaType, flags = link.split('|')

            if mediaType == 'application/pdf':
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

    def storeEpubsInS3(self, record):
        for epubItem in record.has_part:
            itemNo, uri, source, mediaType, flagStr = epubItem.split('|')

            if mediaType == 'application/epub+zip':

                recordID = record.identifiers[0].split('|')[0]

                flags = json.loads(flagStr)

                if flags['download'] is True:
                    bucketLocation = 'epubs/{}/{}.epub'.format(source, recordID)
                    self.addEPUBManifest(
                        record, itemNo, source, flagStr, mediaType, bucketLocation
                    )

                    self.sendFileToProcessingQueue(uri, bucketLocation)
                    break

    def createManifestInS3(self, manifestPath, manifestJSON):
        self.putObjectInBucket(
            manifestJSON.encode('utf-8'), manifestPath, self.s3Bucket
        )

    def addEPUBManifest(self, record, itemNo, source, flagStr, mediaType, location):
            s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, location)

            linkString = '|'.join([itemNo, s3URL, source, mediaType, flagStr])

            record.has_part.insert(0, linkString)

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
    
    @staticmethod
    def fetchPageJSON(url):
        headers = {'Accept': 'application/json'}
        elemResponse = requests.get(url, headers=headers)
        elemResponse.raise_for_status()
        return elemResponse


class LOCError(Exception):
    pass