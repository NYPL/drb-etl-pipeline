import json
import os

from ..core import CoreProcess
from mappings.chicagoISAC import ChicagoISACMapping
from managers import DBManager, S3Manager, WebpubManifest
from logger import create_log
from ..record_buffer import RecordBuffer

logger = create_log(__name__)

class ChicagoISACProcess(CoreProcess):
    def __init__(self, *args):
        super(ChicagoISACProcess, self).__init__(*args[:4])

        self.db_manager = DBManager()

        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.s3Bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):    
        with open('ingestJSONFiles/chicagoISAC_metadata.json') as f:
            chicago_isac_data = json.load(f)

        for meta_dict in chicago_isac_data:
            self.process_chicago_isac_record(meta_dict)

        self.record_buffer.flush()

        logger.info(f'Ingested {len(self.record_buffer.ingest_count)} ISAC records')

    def process_chicago_isac_record(self, record):
        try:
            chicago_isac_rec = ChicagoISACMapping(record)
            chicago_isac_rec.applyMapping()
            self.store_pdf_manifest(chicago_isac_rec.record)
            
            self.record_buffer.add(chicago_isac_rec)
        except Exception:
            logger.exception(ChicagoISACError('Unable to process ISAC record'))
            

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            item_no, uri, source, media_type, flags = link[0].split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]

                manifest_path = 'manifests/{}/{}.json'.format(source, record_id)
                manifest_url = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3Bucket, manifest_path
                )

                manifest_json = self.generate_manifest(record, uri, manifest_url)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json)

                link_string = '|'.join([
                    item_no,
                    manifest_url,
                    source,
                    'application/webpub+json',
                    flags
                ])

                record.has_part.insert(0, link_string)
                self.change_has_part_url_array_to_string(record)

                break
    
    @staticmethod
    def change_has_part_url_array_to_string(record):
        for i in range(1, len(record.has_part)):
            if len(record.has_part[i]) > 1:
                url_array = record.has_part[i]
                record.has_part.pop(i)
                for elem in url_array:
                    record.has_part.append(elem)
            else:
                record.has_part[i] = ''.join(record.has_part[i])

    @staticmethod
    def generate_manifest(record, source_url, manifest_url):
        manifest = WebpubManifest(source_url, 'application/pdf')

        manifest.addMetadata(
            record,
            conformsTo=os.environ['WEBPUB_PDF_PROFILE']
        )
        
        manifest.addChapter(source_url, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_url,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()


class ChicagoISACError(Exception):
    pass
