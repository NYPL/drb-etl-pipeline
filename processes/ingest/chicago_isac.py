import json
import os

from ..core import CoreProcess
from mappings.chicagoISAC import ChicagoISACMapping
from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)

class ChicagoISACProcess(CoreProcess):

    def __init__(self, *args):
        super(ChicagoISACProcess, self).__init__(*args[:4])

        self.fullImport = self.process == 'complete' 

        self.generateEngine()
        self.createSession()

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.createS3Client()

    def run_process(self):    
        with open('ingestJSONFiles/chicagoISAC_metadata.json') as f:
            chicagoISACData = json.load(f)

        for metaDict in chicagoISACData:
            self.process_chicago_isac_record(metaDict)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} ISAC records')

    def process_chicago_isac_record(self, record):
        try:
            chicagoISACRec = ChicagoISACMapping(record)
            chicagoISACRec.applyMapping()
            self.store_pdf_manifest(chicagoISACRec.record)
            self.addDCDWToUpdateList(chicagoISACRec)
            
        except Exception:
            logger.exception(ChicagoISACError('Unable to process ISAC record'))
            

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            itemNo, uri, source, mediaType, flags = link[0].split('|')

            if mediaType == 'application/pdf':
                recordID = record.identifiers[0].split('|')[0]

                manifestPath = 'manifests/{}/{}.json'.format(source, recordID)
                manifestURI = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3Bucket, manifestPath
                )

                manifestJSON = self.generate_manifest(record, uri, manifestURI)

                self.createManifestInS3(manifestPath, manifestJSON)

                linkString = '|'.join([
                    itemNo,
                    manifestURI,
                    source,
                    'application/webpub+json',
                    flags
                ])

                record.has_part.insert(0, linkString)
                self.change_has_part_url_array_to_string(record)

                break
    
    @staticmethod
    def change_has_part_url_array_to_string(record):
        for i in range(1, len(record.has_part)):
            if len(record.has_part[i]) > 1:
                urlArray = record.has_part[i]
                record.has_part.pop(i)
                for elem in urlArray:
                    record.has_part.append(elem)
            else:
                record.has_part[i] = ''.join(record.has_part[i])

    @staticmethod
    def generate_manifest(record, sourceURI, manifestURI):
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
