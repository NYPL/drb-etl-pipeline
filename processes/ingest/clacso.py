import os
import json
import dataclasses
from datetime import datetime, timezone, timedelta
from services import DSpaceService

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

            start_datetime = (
                datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
                if self.process_type == 'daily'
                else self.ingest_period and datetime.strptime(self.ingest_period, '%Y-%m-%dT%H:%M:%S')
            )

            records = self.dspace_service.get_records(
                full_import=True,
                start_timestamp=start_datetime,
                offset=self.offset,
                limit=self.limit
            )
            
            if records:
                for record_mapping in records:
                    self.record_buffer.add(record_mapping.record)
                    self.store_pdf_manifest(record_mapping.record)

            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count if records else 0} CLACSO records')

        except Exception as e:
            logger.exception('Failed to run CLACSO process')
            raise e   
        finally:
            self.db_manager.close_connection()

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            item_no, uri, source, media_type, flags = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]

                manifest_path = 'manifests/{}/{}.json'.format(source, record_id)
                manifest_uri = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3_bucket, manifest_path
                )

                manifest_json = self.generate_manifest(record, uri, manifest_uri)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.s3_bucket)

                link_string = Part(
                    index=item_no, 
                    url=manifest_uri,
                    source=source,
                    file_type='application/pdf',
                    flags=json.dumps(dataclasses.asdict(FileFlags()))
                ).to_string()
                record.has_part.insert(0, link_string)
                break

    @staticmethod
    def generate_manifest(record, source_uri, manifest_urI):
        manifest = WebpubManifest(source_uri, 'application/pdf')

        manifest.addMetadata(record)
        
        manifest.addChapter(source_uri, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_urI,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()
