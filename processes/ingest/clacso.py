import os
import json
import dataclasses
from services import DSpaceService

from digital_assets import get_stored_file_url
from logger import create_log
from managers import S3Manager, WebpubManifest, DBManager
from mappings.clacso import CLACSOMapping
from model import Part, FileFlags
from .record_buffer import RecordBuffer

logger = create_log(__name__)

class CLACSOProcess():
    CLACSO_BASE_URL = 'https://biblioteca-repositorio.clacso.edu.ar/oai/request?'

    def __init__(self, *args):

        self.process_type = args[0]
        self.ingest_period = args[2]
        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(self.db_manager)

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

            records = []

            if self.process_type == 'daily':
                records = self.dspace_service.get_records(offset=self.offset, limit=self.limit)
            elif self.process_type == 'complete':
                records = self.dspace_service.get_records(full_import=True, offset=self.offset, limit=self.limit)
            elif self.process_type == 'custom':
                records = self.dspace_service.get_records(start_timestamp=self.ingest_period, offset=self.offset, limit=self.limit)
            
            if records:
                for record_mapping in records:
                    self.record_buffer.add(record_mapping.record)
                    self.store_pdf_manifest(record_mapping.record)

            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} CLACSO records')

        except Exception as e:
            logger.exception('Failed to run CLACSO process')
            raise e   
        finally:
            self.db_manager.close_connection()

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            item_no, uri, source, media_type, _ = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]

                manifest_path = 'manifests/{}/{}.json'.format(source, record_id)
                manifest_uri = get_stored_file_url(storage_name=self.s3_bucket, file_path=manifest_path)

                manifest_json = self.generate_manifest(record, uri, manifest_uri)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.s3_bucket)

                link_string = Part(
                    index=item_no, 
                    url=manifest_uri,
                    source=source,
                    file_type='application/webpub+json',
                    flags=json.dumps(dataclasses.asdict(FileFlags(reader=True)))
                ).to_string()

                record.has_part.insert(0, link_string)
                break

    @staticmethod
    def generate_manifest(record, source_uri, manifest_uri):
        manifest = WebpubManifest(source_uri, 'application/pdf')

        manifest.addMetadata(record)
        
        manifest.addChapter(source_uri, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_uri,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()
