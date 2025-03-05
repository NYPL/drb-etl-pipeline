import time
import os, requests
import json
import dataclasses
from requests.exceptions import HTTPError, ConnectionError

from ..core import CoreProcess
from mappings.base_mapping import MappingError
from mappings.loc import LOCMapping
from managers import RabbitMQManager, S3Manager, WebpubManifest
from model import get_file_message, FileFlags
from logger import create_log
from datetime import datetime, timedelta, timezone
from digital_assets import get_stored_file_url

logger = create_log(__name__)

LOC_ROOT_OPEN_ACCESS = 'https://www.loc.gov/collections/open-access-books/?fo=json&fa=access-restricted%3Afalse&c=50&at=results&sb=timestamp_desc'
LOC_ROOT_DIGIT = 'https://www.loc.gov/collections/selected-digitized-books/?fo=json&fa=access-restricted%3Afalse&c=50&at=results&sb=timestamp_desc' 

class LOCProcess(CoreProcess):

    def __init__(self, *args):
        super(LOCProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.process == 'complete'
        self.startTimestamp = None 

        self.generateEngine()
        self.createSession()

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3Bucket = os.environ['FILE_BUCKET']

        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.fileQueue, self.fileRoute)

    def runProcess(self):
        if self.process == 'weekly':
            startTimeStamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
            self.importLOCRecords(startTimeStamp)
        elif self.process == 'complete':
            self.importLOCRecords()
        elif self.process == 'custom':
            timeStamp = self.ingestPeriod
            startTimeStamp = datetime.strptime(timeStamp, '%Y-%m-%dT%H:%M:%S')
            self.importLOCRecords(startTimeStamp)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} LOC records')
    

    def importLOCRecords(self, startTimeStamp=None):

        openAccessRequestCount = 0 
        digitizedRequestCount = 0

        try:
            openAccessRequestCount = self.importOpenAccessRecords(openAccessRequestCount, startTimeStamp)
            logger.debug('Open Access Collection Ingestion Complete')

        except Exception or HTTPError as e:
            logger.exception(e)

        try:
            digitizedRequestCount = self.importDigitizedRecords(digitizedRequestCount, startTimeStamp)
            logger.debug('Digitized Books Collection Ingestion Complete')
        
        except Exception or HTTPError as e:
            logger.exception(e)

        

    def importOpenAccessRecords(self, count, customTimeStamp):
        sp = 1
        try:

            whileBreakFlag = False
            
            # An HTTP error will occur when the sp parameter value
            # passes the last page number of the collection search reuslts
            while sp < 100000:
                if self.ingestLimit and count >= self.ingestLimit:
                    break

                openAccessURL = '{}&sp={}'.format(LOC_ROOT_OPEN_ACCESS, sp)
                jsonData = self.fetchPageJSON(openAccessURL)
                LOCData = jsonData.json()

                for metaDict in LOCData['results']:
                    #Weekly/Custom Ingestion Conditional
                    if customTimeStamp:
                        itemTimeStamp = datetime.strptime(metaDict['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

                        if itemTimeStamp < customTimeStamp:
                            whileBreakFlag = True
                            break

                    if 'resources' in metaDict.keys():
                        if metaDict['resources']:
                            resources = metaDict['resources'][0]
                            if 'pdf' in resources.keys() or 'epub_file' in resources.keys():
                                logger.debug(f'OPEN ACCESS URL: {openAccessURL}')
                                logger.debug(f"TITLE: {metaDict['title']}")

                                self.processLOCRecord(metaDict)
                                count += 1

                                logger.debug(f'Count for OP Access: {count}')

                if whileBreakFlag == True:
                    logger.debug('No new items added to collection')
                    break

                sp += 1
                time.sleep(5)

        except Exception or HTTPError or IndexError or KeyError as e:
            logger.exception(e)

        return count

    def importDigitizedRecords(self, count, customTimeStamp):
        sp = 1
        try:

            whileBreakFlag = False

            # An HTTP error will occur when the sp parameter value
            # passes the last page number of the collection search reuslts
            while sp < 100000:
                if self.ingestLimit and count >= self.ingestLimit:
                    break

                digitizedURL = '{}&sp={}'.format(LOC_ROOT_DIGIT, sp)
                jsonData = self.fetchPageJSON(digitizedURL)
                LOCData = jsonData.json()

                for metaDict in LOCData['results']:
                    #Weekly Ingestion conditional
                    if customTimeStamp:
                        itemTimeStamp = datetime.strptime(metaDict['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ')

                        if itemTimeStamp < customTimeStamp:
                            whileBreakFlag = True
                            break

                    if 'resources' in metaDict.keys():
                        if metaDict['resources']:
                            resources = metaDict['resources'][0]
                            if 'pdf' in resources.keys() or 'epub_file' in resources.keys():
                                logger.debug(f'DIGITIZED URL: {digitizedURL}')
                                logger.debug(f"TITLE: {metaDict['title']}")

                                self.processLOCRecord(metaDict)
                                count += 1

                                logger.debug(f'Count for Digitized: {count}')
            
                if whileBreakFlag == True:
                    logger.debug('No new items added to collection')
                    break

                sp += 1
                time.sleep(5)
                
            return count
        
        except Exception or HTTPError or IndexError or KeyError as e:
            logger.exception(e)

    def processLOCRecord(self, record):
        try:
            LOCRec = LOCMapping(record)
            LOCRec.applyMapping()

            if LOCRec.record.authors is None:
                logger.warning(f'Unable to map author in LOC record {LOCRec.record} ')
                return
            
            webpub_flags = json.dumps(dataclasses.asdict(FileFlags(reader=True)))
            self.addHasPartMapping(record, LOCRec.record)
            self.s3_manager.store_pdf_manifest(LOCRec.record, self.s3Bucket, flags=webpub_flags)
            self.storeEpubsInS3(LOCRec.record)
            self.addDCDWToUpdateList(LOCRec)
        except Exception:
            logger.exception(f'Unable to process LOC record')
            
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

    def storeEpubsInS3(self, record):
        for epubItem in record.has_part:
            itemNo, uri, source, mediaType, flagStr = epubItem.split('|')

            if mediaType == 'application/epub+zip':

                recordID = record.identifiers[0].split('|')[0]

                bucketLocation = 'epubs/{}/{}.epub'.format(source, recordID)
                self.addEPUBManifest(
                    record, itemNo, source, flagStr, mediaType, bucketLocation
                )

                self.rabbitmq_manager.sendMessageToQueue(self.fileQueue, self.fileRoute, get_file_message(uri, bucketLocation))
                break

    def addEPUBManifest(self, record, itemNo, source, flagStr, mediaType, location):
            s3_url = get_stored_file_url(storage_name=self.s3Bucket, file_path=location)

            link_string = '|'.join([itemNo, s3_url, source, mediaType, flagStr])

            record.has_part.insert(0, link_string)
    
    @staticmethod
    def fetchPageJSON(url):
        headers = {'Accept': 'application/json'}
        elemResponse = requests.get(url, headers=headers)
        elemResponse.raise_for_status()
        return elemResponse


class LOCError(Exception):
    pass
