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

class ChicagoISACProcess(CoreProcess):

    def __init__(self, *args):
        super(ChicagoISACProcess, self).__init__(*args[:4])

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
        with open('chicagoISAC_metadata.json') as f:
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
            
        except (MappingError, HTTPError, ConnectionError, IndexError, TypeError) as e:
            logger.exception(e)
            logger.warn(ChicagoISACError('Unable to process ISAC record'))
            

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
                #The second element of the has_part array will always be an array of pdfURLS from the json file
                #Those elements of the array are popped out and appended back into the has_part array as strings instead of an array
                for i in range(1, len(record.has_part)):
                    if len(record.has_part[i]) > 1:
                        urlArray = record.has_part[i]
                        record.has_part.pop(i)
                        for elem in urlArray:
                            record.has_part.append(elem)
                    else:
                        record.has_part[i] = ''.join(record.has_part[i])
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


class ChicagoISACError(Exception):
    pass
