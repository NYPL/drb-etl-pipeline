from datetime import datetime, timedelta
import json
import mimetypes
import os
import re

from .core import CoreProcess
from managers import GutenbergManager
from mappings.gutenberg import GutenbergMapping


class GutenbergProcess(CoreProcess):
    GUTENBERG_NAMESPACES = {
        'dcam': 'http://purl.org/dc/dcam/',
        'dcterms': 'http://purl.org/dc/terms/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'cc': 'http://web.resource.org/cc/',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'pgterms': 'http://www.gutenberg.org/2009/pgterms/'
    }

    def __init__(self, *args):
        super(GutenbergProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5]) or 0
        self.ingestLimit = (int(args[4]) + self.ingestOffset) or 5000

        # Connect to database
        self.generateEngine()
        self.createSession()

        # Connect to epub processing queue
        self.fileQueue = os.environ['FILE_QUEUE']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.fileQueue)

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']

    def runProcess(self):
        if self.process == 'daily':
            self.importRDFRecords()
        elif self.process == 'complete':
            self.importRDFRecords(fullImport=True)
        elif self.process == 'custom':
            self.importRDFRecords(startTimestamp=self.ingestPeriod)

        self.saveRecords()
        self.commitChanges()
    
    def importRDFRecords(self, fullImport=False, startTimestamp=None):
        orderDirection = 'DESC'
        orderField = 'PUSHED_AT'
        if not fullImport:
            if not startTimestamp:
                startTimestamp = datetime.utcnow() - timedelta(days=1)
            else:
                startTimestamp = datetime.strptime(startTimestamp, '%Y-%m-%dT%H:%M:%S')
        else:
            orderDirection = 'ASC'
            orderField = 'CREATED_AT'

        pageSize = 100
        currentPosition = 0
        manager = GutenbergManager(orderDirection, orderField, startTimestamp, pageSize)

        while True:
            continuation = manager.fetchGithubRepoBatch()

            currentPosition += pageSize
            if currentPosition <= self.ingestOffset: continue

            manager.fetchMetadataFilesForBatch()

            self.processGutenbergBatch(manager.dataFiles)

            manager.resetBatch()

            if not continuation or currentPosition >= self.ingestLimit: break

    def processGutenbergBatch(self, dataFiles):
        for (gutenbergRDF, gutenbergYAML) in dataFiles:
            gutenbergRec = GutenbergMapping(
                gutenbergRDF,
                self.GUTENBERG_NAMESPACES,
                self.statics
            )

            gutenbergRec.applyMapping()

            self.storeEpubsInS3(gutenbergRec)
            self.addCoverAndStoreInS3(gutenbergRec, gutenbergYAML)
            
            self.addDCDWToUpdateList(gutenbergRec)

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
                bucketLocation = 'epubs/{}/{}_{}/oebps/content.opf'.format(source, gutenbergID, gutenbergType)

            s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, bucketLocation)

            gutenbergRec.record.has_part[i] = '|'.join([pos, s3URL, source, mediaType, flagStr])

            if flags['download'] is True:
                self.sendFileToProcessingQueue(gutenbergURL, bucketLocation)

    def addCoverAndStoreInS3(self, gutenbergRec, yamlData):
        for coverData in yamlData['covers']:
            if coverData['cover_type'] == 'generated': continue

            mimeType, _ = mimetypes.guess_type(coverData['image_path'])
            gutenbergID = yamlData['identifiers']['gutenberg']

            fileExt = re.search(r'(\.[a-z0-9]+)$', coverData['image_path']).group(1)
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
        self.sendMessageToQueue(self.fileQueue, s3Message)
