import os
from typing import Optional

from digital_assets import get_stored_file_url
from managers import DBManager, RabbitMQManager, S3Manager
from model import get_file_message, Record, Part, FileFlags, Source
from logger import create_log
from ..record_buffer import RecordBuffer
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
            self.s3_manager.store_pdf_manifest(record=record_mapping.record, bucket_name=self.s3_bucket)

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

        record.has_part.append(str(Part(
            url=file_url,
            source=Source.MET.value,
            file_type=file_type,
            flags=str(FileFlags(cover=True))
        )))

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
