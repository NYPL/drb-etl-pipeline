import os

from digital_assets import get_stored_file_url
from managers import DBManager, RabbitMQManager, S3Manager, WebpubManifest
from model import get_file_message, Part, Record, FileFlags
from logger import create_log
from ..record_buffer import RecordBuffer
from .. import utils
from services import LOCService

logger = create_log(__name__)


class LOCProcess():

    def __init__(self, *args):
        self.process_type = args[0]
        self.ingest_period = args[2]

        self.offset = int(args[5] or 0)
        self.limit = (int(args[4]) + self.offset) if args[4] else 5000
        self.startTimestamp = None 

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.loc_service = LOCService()

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.file_queue, self.file_route)

    def runProcess(self):
        start_datetime = utils.get_start_datetime(
            process_type=self.process_type,
            ingest_period=self.ingest_period
        )

        records = self.loc_service.get_records(
            start_timestamp=start_datetime,
            limit=self.limit,
        )

        for record in records:
            self.store_pdf_manifest(record=record)
            self.store_epub(record=record)

            self.record_buffer.add(record=record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} LOC records')

    def store_pdf_manifest(self, record: Record):
        record_id = record.source_id.split('|')[0]
        pdf_part = next(filter(lambda part: part.file_type == 'application/pdf', record.get_parts()), None)

        if pdf_part is not None:
            manifest_path = f'manifests/{record.source}/{record_id}'
            manifest_url = get_stored_file_url(storage_name=self.s3_bucket, file_path=manifest_path)
            manifest_json = self.generate_manifest(record=record, source_uri=pdf_part.url, manifest_uri=manifest_url)

            self.s3_manager.createManifestInS3(manifestPath=manifest_path, manifestJSON=manifest_json, s3_bucket=self.s3_bucket)

            record.has_part.insert(0, Part(
                index=pdf_part.index,
                url=manifest_url,
                source=record.source,
                file_type='application/webpub+json',
                flags=FileFlags(reader=True).to_string()
            ).to_string())

    def store_epub(self, record: Record):
        record_id = record.source_id.split('|')[0]
        epub_part = next(filter(lambda part: part.file_type == 'application/epub+zip', record.get_parts()), None)

        if epub_part is not None:
            epub_location = f'epubs/{epub_part.source}/{record_id}.epub'
            epub_url = get_stored_file_url(storage_name=epub_url, file_path=epub_location)

            record.has_part = [Part(
                index=epub_part.index,
                url=epub_url,
                source=record.source,
                file_type=epub_part.file_type,
                flags=epub_part.flags
            ).to_string()]

            self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(epub_part.url, epub_location))

    @staticmethod
    def generate_manifest(record: Record, source_uri: str, manifest_uri: str):
        manifest = WebpubManifest(source_uri, 'application/pdf')

        manifest.addMetadata(record)
        
        manifest.addChapter(source_uri, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_uri,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()
