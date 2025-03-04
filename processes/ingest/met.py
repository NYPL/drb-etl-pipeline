import dataclasses
import json
import os
from typing import Optional

from digital_assets import get_stored_file_url
from managers import DBManager, RabbitMQManager, S3Manager, WebpubManifest
from model import get_file_message, Record, Part, FileFlags, Source
from logger import create_log
from .record_buffer import RecordBuffer
from services import METService
from .. import utils

logger = create_log(__name__)


class METProcess():
    MET_ROOT_URL = 'https://libmma.contentdm.oclc.org/digital'

    def __init__(self, *args):
        self.process = args[0]
        self.ingest_period = args[2]

        self.offset = int(args[5] or 0)
        self.limit = (int(args[4]) + self.offset) if args[4] else 5000

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.met_service = METService()

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.file_queue, self.file_route)

        self.s3_bucket = os.environ['FILE_BUCKET']
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

    def runProcess(self):
        record_mappings = self.met_service.get_records(
            start_timestamp=utils.get_start_datetime(process_type=self.process, ingest_period=self.ingest_period),
            limit=self.limit,
            offset=self.offset
        )

        for record_mapping in record_mappings:
            self.store_pdf_manifest(record=record_mapping.record)

            try:
                self.add_cover(record=record_mapping.record, file_type=record_mapping.file_type)
            except Exception:
                pass

            self.record_buffer.add(record=record_mapping.record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} MET records')

    def add_cover(self, record: Record, file_type: Optional[str]=None):
        record_id = record.source_id.split('|')[0]
        cover_path = self.get_cover_path(file_type=file_type, record_id=record_id)

        if cover_path is None:
            return

        cover_source_url = f'{self.MET_ROOT_URL}/{cover_path}'
        file_path = f'covers/met/{record_id}.{cover_source_url[-3:]}'
        file_url = get_stored_file_url(storage_name=self.s3_bucket, file_path=file_path)
        file_type = 'image/jpeg' if cover_source_url[-3:] == 'jpg' else 'image/png'

        record.has_part.append(Part(
            url=file_url,
            source=Source.MET.value,
            file_type=file_type,
            flags=json.dumps(dataclasses.asdict(FileFlags(cover=True)))
        ).to_string())

        self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(cover_source_url, file_path))

    def get_cover_path(self, file_type: Optional[str], record_id: str) -> Optional[str]:
        if file_type == 'cpd':
            try:
                compound_record_object = self.met_service.query_met_api(query=METService.COMPOUND_QUERY.format(record_id))

                cover_id = compound_record_object['page'][0]['pageptr']

                image_object = self.met_service.query_met_api(query=METService.IMAGE_QUERY.format(cover_id))

                return image_object.get('imageUri')
            except Exception:
                logger.exception(f'Unable to get cover path for record: {record_id}')
                return None
        
        return f'api/singleitem/image/pdf/p15324coll10/{record_id}/default.png'

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
                flags=pdf_part.flags
            ).to_string())

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
