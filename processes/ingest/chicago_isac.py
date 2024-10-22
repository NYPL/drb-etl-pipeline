import json
import os

from ..core import CoreProcess
from mappings.chicagoISAC import ChicagoISACMapping
from managers import DBManager, ElasticsearchManager, RedisManager, S3Manager, WebpubManifest
from logger import createLog

logger = createLog(__name__)

class ChicagoISACProcess(CoreProcess):

    def __init__(self, *args):

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete' 

        self.db_manager = DBManager()
        self.elastic_search_manager = ElasticsearchManager()
        self.redis_manager = RedisManager()

        self.generateEngine()
        self.createSession()

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()

    def runProcess(self):
        
        logger.info('Starting ISAC process...')

        self.db_manager.generateEngine()
        self.redis_manager.createRedisClient()
        self.elastic_search_manager.createElasticConnection()
        self.s3_manager.createS3Client()
        
        with open('ingestJSONFiles/chicagoISAC_metadata.json') as f:
                chicagoISACData = json.load(f)

        for metaDict in chicagoISACData:
            self.processChicagoISACRecord(metaDict)

        self.saveRecords()
        self.commitChanges()

    def processChicagoISACRecord(self, record):
        try:
            chicagoISACRec = ChicagoISACMapping(record)
            chicagoISACRec.applyMapping()
            self.storePDFManifest(chicagoISACRec.record)
            self.addDCDWToUpdateList(chicagoISACRec)
            
        except Exception as e:
            logger.exception(e)
            logger.warning(ChicagoISACError('Unable to process ISAC record'))
            

    def storePDFManifest(self, record):
        for link in record.has_part:
            itemNo, uri, source, mediaType, flags = link[0].split('|')

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
                self.hasPartArrayElemToStringElem(record)

                break
    
    @staticmethod
    def hasPartArrayElemToStringElem(record):
        for i in range(1, len(record.has_part)):
            if len(record.has_part[i]) > 1:
                urlArray = record.has_part[i]
                record.has_part.pop(i)
                for elem in urlArray:
                    record.has_part.append(elem)
            else:
                record.has_part[i] = ''.join(record.has_part[i])

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


class ChicagoISACError(Exception):
    pass
