import json
import os
from requests.exceptions import HTTPError, ConnectionError

from ..core import CoreProcess
from mappings.base_mapping import MappingError
from mappings.UofSC import UofSCMapping
from managers import DBManager, S3Manager, WebpubManifest
from logger import create_log
from ..record_buffer import RecordBuffer

logger = create_log(__name__)

class UofSCProcess(CoreProcess):

    def __init__(self, *args):
        super(UofSCProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5] or 0)
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 5000
        self.fullImport = self.process == 'complete' 

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):
        with open('UofSC_metadata.json') as f:
                UofSCData = json.load(f)

        for metaDict in UofSCData:
            self.processUofSCRecord(metaDict)

        self.record_buffer.flush()

    def processUofSCRecord(self, record):
        try:
            UofSCRec = UofSCMapping(record)
            UofSCRec.applyMapping()
            self.storePDFManifest(UofSCRec.record)
            
            self.record_buffer.add(UofSCRec)
        except (MappingError, HTTPError, ConnectionError, IndexError, TypeError) as e:
            logger.exception(e)
            logger.warn(UofSCError('Unable to process UofSC record'))
            

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

                self.s3_manager.createManifestInS3(manifestPath, manifestJSON)

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


class UofSCError(Exception):
    pass
