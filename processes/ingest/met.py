from datetime import datetime, timedelta, timezone
import json
import os
import requests
from requests.exceptions import HTTPError, ConnectionError

from ..core import CoreProcess
from mappings.base_mapping import MappingError
from mappings.met import METMapping
from managers import RabbitMQManager, S3Manager, WebpubManifest
from model import get_file_message
from logger import create_log

logger = create_log(__name__)


class METProcess(CoreProcess):
    MET_ROOT_URL = 'https://libmma.contentdm.oclc.org/digital'

    # The documentation for these API queries is here: https://help.oclc.org/Metadata_Services/CONTENTdm/Advanced_website_customization/API_Reference/CONTENTdm_API/CONTENTdm_Server_API_Functions_-_dmwebservices
    LIST_QUERY = 'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/p15324coll10/CISOSEARCHALL/title!dmmodified!dmcreated!rights/dmmodified/{}/{}/1/0/0/00/0/json'
    DETAIL_QUERY = 'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetItemInfo/p15324coll10/{}/json'
    COMPOUND_QUERY = 'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetCompoundObjectInfo/p15324coll10/{}/json'
    IMAGE_QUERY = 'https://libmma.contentdm.oclc.org/digital/api/singleitem/collection/p15324coll10/id/{}'

    def __init__(self, *args):
        super(METProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete'
        self.startTimestamp = None

        self.generateEngine()
        self.createSession()

        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.fileQueue, self.fileRoute)

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):
        self.setStartTime()
        self.importDCRecords()

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} MET records')

    def setStartTime(self):
        if not self.fullImport:
            if not self.ingestPeriod:
                self.startTimestamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1)
            else:
                self.startTimestamp = datetime.strptime(
                    self.ingestPeriod, '%Y-%m-%dT%H:%M:%S'
                )

    def importDCRecords(self):
        currentPosition = self.ingestOffset
        pageSize = 50

        while True:
            batchQuery = self.LIST_QUERY.format(pageSize, currentPosition)

            batchResponse = self.queryMetAPI(batchQuery)

            batchRecords = batchResponse['records']

            self.processMetBatch(batchRecords)

            if len(batchRecords) < 1 or currentPosition >= self.ingestLimit:
                break

            currentPosition += pageSize

    def processMetBatch(self, metRecords):
        for record in metRecords:
            if (
                self.startTimestamp
                and datetime.strptime(record['dmmodified'], '%Y-%m-%d')
                >= self.startTimestamp
            ) or record['rights'] == 'copyrighted':
                continue

            try:
                self.processMetRecord(record)
            except METError:
                logger.warning('Unable to process MET record {}'.format(
                    record['pointer'])
                )

    def processMetRecord(self, record):
        try:
            detailQuery = self.DETAIL_QUERY.format(record['pointer'])
            metDetail = self.queryMetAPI(detailQuery)

            metRec = METMapping(metDetail)
            metRec.applyMapping()
        except (MappingError, HTTPError, ConnectionError) as e:
            logger.debug(e)
            raise METError('Unable to process MET record')

        self.storePDFManifest(metRec.record)

        try:
            self.addCoverAndStoreInS3(metRec.record, record['filetype'])
        except METError as e:
            logger.warning('Unable to fetch cover ({})'.format(e))

        self.addDCDWToUpdateList(metRec)

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

        self.rabbitmq_manager.sendMessageToQueue(self.fileQueue, self.fileRoute, get_file_message(sourceURL, bucketLocation))

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
                raise METError('Unable to fetch page structure for record')

            return imageObject['imageUri']
        else:
            return 'api/singleitem/image/pdf/p15324coll10/{}/default.png'.format(recordID)

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

                self.s3_manager.createManifestInS3(manifestPath, manifestJSON, self.s3Bucket)

                linkString = '|'.join([
                    itemNo,
                    manifestURI,
                    source,
                    'application/webpub+json',
                    flags
                ])
                record.has_part.insert(0, linkString)

                break

    @staticmethod
    def generateManifest(record, sourceURI, manifestURI):
        manifest = WebpubManifest(sourceURI, 'application/pdf')

        manifest.addMetadata(record)

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


class METError(Exception):
    pass
