import os
import json
import dataclasses
from services import DSpaceService

from ..core import CoreProcess
from logger import create_log
from managers import S3Manager, WebpubManifest
from mappings.clacso import CLACSOMapping
from model import Part, FileFlags


logger = create_log(__name__)

class CLACSOProcess(CoreProcess):
    CLACSO_BASE_URL = 'https://biblioteca-repositorio.clacso.edu.ar/oai/request?'

    def __init__(self, *args):
        super(CLACSOProcess, self).__init__(*args[:4])

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.offset = int(args[5]) if args[5] else 0
        self.limit = (int(args[4]) + self.offset) if args[4] else 10000

        self.dspace_service = DSpaceService(base_url=self.CLACSO_BASE_URL, source_mapping=CLACSOMapping)
        
    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            records = []

            if self.process == 'daily':
                records = self.dspace_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process == 'complete':
                records = self.dspace_service.get_records(full_import=True, offset=self.offset, limit=self.limit)
            elif self.process == 'custom':
                records = self.dspace_service.get_records(start_timestamp=self.ingestPeriod, offset=self.offset, limit=self.limit)
            else: 
                logger.warning(f'Unknown CLACSO ingestion process type {self.process}')
                return
            
            if records:
                for record in records:
                    self.store_pdf_manifest(record)
                    self.addDCDWToUpdateList(record)

            self.saveRecords()
            self.commitChanges()

            logger.info(f'Ingested {len(self.records) if records else 0} CLACSO records')

        except Exception as e:
            logger.exception('Failed to run CLACSO process')
            raise e   
        finally:
            self.close_connection()

    def store_pdf_manifest(self, record):
        for link in record.record.has_part:
            item_no, uri, source, media_type, flags = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.record.identifiers[0].split('|')[0]

                manifest_path = 'manifests/{}/{}.json'.format(source, record_id)
                manifest_uri = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3_bucket, manifest_path
                )

                manifest_json = self.generate_manifest(record.record, uri, manifest_uri)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.s3_bucket)

                link_string = Part(
                    index=item_no, 
                    url=manifest_uri,
                    source=source,
                    file_type='application/pdf',
                    flags=json.dumps(dataclasses.asdict(FileFlags()))
                ).to_string()
                record.record.has_part.insert(0, link_string)
                break

    @staticmethod
    def generate_manifest(record, sourceURI, manifest_urI):
        manifest = WebpubManifest(sourceURI, 'application/pdf')

        manifest.addMetadata(record)
        
        manifest.addChapter(sourceURI, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_urI,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()
