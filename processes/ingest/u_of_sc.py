import json
import os
from requests.exceptions import HTTPError, ConnectionError

from ..core import CoreProcess
from mappings.core import MappingError
from mappings.UofSC import UofSCMapping
from managers import WebpubManifest
from logger import create_logger

logger = create_logger(__name__)

class UofSCProcess(CoreProcess):

    def __init__(self, *args):
        super(UofSCProcess, self).__init__(*args[:4])

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
        with open('UofSC_metadata.json') as f:
                UofSCData = json.load(f)

        for metaDict in UofSCData:
            self.processUofSCRecord(metaDict)

        self.saveRecords()
        self.commitChanges()

    def processUofSCRecord(self, record):
        try:
            UofSCRec = UofSCMapping(record)
            UofSCRec.applyMapping()
            self.storePDFManifest(UofSCRec.record)
            self.addDCDWToUpdateList(UofSCRec)
            
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
