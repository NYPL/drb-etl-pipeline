import json
import os
import requests
from requests.exceptions import HTTPError, ConnectionError

from .core import CoreProcess
from mappings.core import MappingError
from mappings.chicagoISAC import ChicagoISACMapping
from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)


class ChiacgoISACProcess(CoreProcess):

    def __init__(self, *args):
        super(ChiacgoISACProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete'

        # Connect to database
        self.generateEngine()
        self.createSession()

        # Connect to file processing queue
        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']
        self.createOrConnectQueue(self.fileQueue, self.fileRoute)

        # S3 Configuration
        self.s3Bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def runProcess(self):
        self.processChicagoISACRecord()

        self.saveRecords()
        self.commitChanges()

    def processChicagoISACRecord(self, record):
        try:
            with open('data_file.json') as f:
                chicagoISACData = json.load(f)

            chicagoISACRec = ChicagoISACMapping(chicagoISACData)
            chicagoISACRec.applyMapping()
            
        except (MappingError, HTTPError, ConnectionError) as e:
            logger.debug(e)
            raise ChicagoISACError('Unable to process MET record')

        self.storePDFManifest(chicagoISACRec.record)

        try:
            self.addCoverAndStoreInS3(chicagoISACRec.record, record['filetype'])
        except ChicagoISACError as e:
            logger.warning('Unable to fetch cover ({})'.format(e))

        self.addDCDWToUpdateList(chicagoISACRec)

    def addCoverAndStoreInS3(self, record, filetype):
        recordID = record.identifiers[0].split('|')[0]

        coverPath = self.setCoverPath(filetype, recordID)

        sourceURL = '{}/{}'.format(self.MET_ROOT_URL, coverPath)

        bucketLocation = 'covers/met/{}.{}'.format(recordID, sourceURL[-3:])

        s3URL = 'https://{}.s3.amazonaws.com/{}'.format(
            self.s3Bucket, bucketLocation
        )

        fileType = 'image/jpeg' if sourceURL[-3:] == 'jpg' else 'image/png'

        record.has_part.append(
            '|'.join(['', s3URL, 'met', fileType, json.dumps({'cover': True})])
        )

        self.sendFileToProcessingQueue(sourceURL, bucketLocation)

    def setCoverPath(self, filetype, recordID):
        if filetype == 'cpd':
            try:
                compoundQuery = self.COMPOUND_QUERY.format(recordID)
                compoundObject = self.queryMetAPI(compoundQuery)

                coverID = compoundObject['page'][0]['pageptr']

                imageQuery = self.IMAGE_QUERY.format(coverID)
                imageObject = self.queryMetAPI(imageQuery)
            except (KeyError, HTTPError):
                logger.debug(
                    'Unable to parse compound structure for {}'.format(
                        recordID
                    )
                )
                raise ChicagoISACError('Unable to fetch page structure for record')

            return imageObject['imageUri']
        else:
            return 'api/singleitem/image/pdf/p15324coll10/{}/default.png'.format(recordID)

    def sendFileToProcessingQueue(self, fileURL, s3Location):
        s3Message = {
            'fileData': {
                'fileURL': fileURL,
                'bucketPath': s3Location
            }
        }
        self.sendMessageToQueue(self.fileQueue, self.fileRoute, s3Message)

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
                    flags
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

    @staticmethod
    def queryMetAPI(query, method='GET'):
        method = method.upper()

        response = requests.request(method, query, timeout=30)

        response.raise_for_status()

        if method == 'HEAD':
            return response.status_code
        else:
            return response.json()


class ChicagoISACError(Exception):
    pass
