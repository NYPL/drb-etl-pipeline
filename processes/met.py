from datetime import datetime, timedelta
import json
import mimetypes
import os
import re
from time import strptime
import requests

from .core import CoreProcess
from mappings.gutenberg import GutenbergMapping


class METProcess(CoreProcess):
    # The format for this query is documented here: https://help.oclc.org/Metadata_Services/CONTENTdm/Advanced_website_customization/API_Reference/CONTENTdm_API/CONTENTdm_Server_API_Functions_-_dmwebservices
    LIST_QUERY = 'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/p15324coll10/CISOSEARCHALL/title!dmmodified!dmcreated/dmmodified/{}/{}/1/0/0/00/0/json'
    DETAIL_QUERY = 'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetItemInfo/p15324coll10/{}/json'

    def __init__(self, *args):
        super(METProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete'
        self.startTimestamp = None

        # Connect to database
        self.generateEngine()
        self.createSession()

        # Connect to file processing queue
        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']
        # self.createRabbitConnection()
        # self.createOrConnectQueue(self.fileQueue, self.fileRoute)

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']

    def runProcess(self):
        self.setStartTime()
        self.importDCRecords()

        self.saveRecords()
        self.commitChanges()

    def setStartTime(self):
        if not self.fullImport:
            if not self.ingestPeriod:
                self.startTimestamp = datetime.utcnow() - timedelta(days=1)
            else:
                self.startTimestamp = datetime.strptime(self.ingestPeriod, '%Y-%m-%dT%H:%M:%S')
    
    def importDCRecords(self):
        currentPosition = self.ingestOffset
        pageSize = 10

        while True:
            batchQuery = self.LIST_QUERY.format(pageSize, currentPosition)

            batchResponse = self.queryMetAPI(batchQuery)

            batchRecords = batchResponse['records']

            self.processMetBatch(batchRecords)

            if len(batchRecords) < 0 or currentPosition >= self.ingestLimit: break

            currentPosition += pageSize
            break

    def processMetBatch(self, metRecords):
        for record in metRecords:

            if self.startTimestamp \
                and strptime(record['dmmodified'], '%Y-%m-%d') >= self.startTimestamp:
                continue

            detailQuery = self.DETAIL_QUERY.format(record['pointer'])
            metDetail = self.queryMetAPI(detailQuery)

            print(metDetail)
            
            # self.addDCDWToUpdateList(gutenbergRec)

    def storeEpubsInS3(self, gutenbergRec):
        for i, epubItem in enumerate(gutenbergRec.record.has_part):
            pos, gutenbergURL, source, mediaType, flagStr = epubItem.split('|')

            epubIDParts = re.search(r'\/([0-9]+).epub.([a-z]+)$', gutenbergURL)
            gutenbergID = epubIDParts.group(1)
            gutenbergType = epubIDParts.group(2)

            flags = json.loads(flagStr)

            if flags['download'] is True:
                bucketLocation = 'epubs/{}/{}_{}.epub'.format(source, gutenbergID, gutenbergType)
            else:
                bucketLocation = 'epubs/{}/{}_{}/META-INF/content.xml'.format(source, gutenbergID, gutenbergType)
                mediaType = 'application/epub+xml'

            s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, bucketLocation)

            gutenbergRec.record.has_part[i] = '|'.join([pos, s3URL, source, mediaType, flagStr])

            if flags['download'] is True:
                self.sendFileToProcessingQueue(gutenbergURL, bucketLocation)

    def addCoverAndStoreInS3(self, gutenbergRec, yamlData):
        for coverData in yamlData['covers']:
            if coverData['cover_type'] == 'generated': continue

            mimeType, _ = mimetypes.guess_type(coverData['image_path'])
            gutenbergID = yamlData['identifiers']['gutenberg']

            fileExt = re.search(r'(\.[a-zA-Z0-9]+)$', coverData['image_path']).group(1)
            bucketLocation = 'covers/gutenberg/{}{}'.format(gutenbergID, fileExt)

            s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, bucketLocation)

            gutenbergRec.record.has_part.append(
                '|'.join(['', s3URL, 'gutenberg', mimeType, json.dumps({'cover': True})])
            )

            sourceRoot = yamlData['url'].replace('ebooks', 'files')
            sourceURL = '{}/{}'.format(sourceRoot, coverData['image_path'])

            self.sendFileToProcessingQueue(sourceURL, bucketLocation)

    def sendFileToProcessingQueue(self, fileURL, s3Location):
        s3Message = {
            'fileData': {
                'fileURL': fileURL,
                'bucketPath': s3Location
            }
        }
        self.sendMessageToQueue(self.fileQueue, self.fileRoute, s3Message)

    @staticmethod
    def queryMetAPI(query):
        response = requests.get(query, timeout=30)

        response.raise_for_status()

        return response.json()
