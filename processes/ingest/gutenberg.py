import dataclasses
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
import re

from digital_assets import get_stored_file_url
from mappings.gutenberg import GutenbergMapping
from managers import DBManager, RabbitMQManager
from model import get_file_message, FileFlags, Part, Source
from logger import create_log
from ..record_buffer import RecordBuffer
from services import GutenbergService

logger = create_log(__name__)


class GutenbergProcess():
    def __init__(self, *args):
        self.process_type = args[0]
        self.ingest_period = args[2]

        self.offset = int(args[5] or 0)
        self.limit = (int(args[4]) + self.offset) if args[4] else 5000

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.file_queue, self.file_route)

        self.file_bucket = os.environ['FILE_BUCKET']

        self.gutenberg_service = GutenbergService()

    def runProcess(self):
        start_datetime = (
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            if self.process_type == 'daily'
            else self.ingest_period and datetime.strptime(self.ingest_period, '%Y-%m-%dT%H:%M:%S')
        )

        records = self.gutenberg_service.get_records(
            start_timestamp=start_datetime,
            offset=self.offset,
            limit=self.limit
        )

        for record_mapping in records:
            self.store_epubs(record_mapping)

            try:
                self.add_cover(record_mapping)
            except Exception:
                logger.warning(f'Unable to store cover for {record_mapping.record.source_id}')

            self.record_buffer.add(record_mapping.record)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} Gutenberg records')

    def store_epubs(self, gutenberg_record: GutenbergMapping):
        epub_parts = []

        for part in gutenberg_record.record.get_parts():
            epub_id_parts = re.search(r'\/([0-9]+).epub.([a-z]+)$', part.url)
            gutenberg_id = epub_id_parts.group(1)
            gutenberg_type = epub_id_parts.group(2)

            if json.loads(part.flags).get('download', False) is True:
                epub_path = f'epubs/{part.source}/{gutenberg_id}_{gutenberg_type}.epub'
                epub_url = get_stored_file_url(self.file_bucket, epub_path)

                epub_parts.append(Part(
                    index=part.index,
                    source=part.source,
                    url=epub_url,
                    file_type=part.file_type,
                    flags=part.flags
                ).to_string())

                self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(part.url, epub_path))
            else:
                container_path = f'epubs/{part.source}/{gutenberg_id}_{gutenberg_type}/META-INF/container.xml'
                manifest_path = f'epubs/{part.source}/{gutenberg_id}_{gutenberg_type}/manifest.json'

                epub_parts.append(Part(
                    index=part.index,
                    source=part.source,
                    url=get_stored_file_url(self.file_bucket, container_path),
                    file_type='application/epub+xml',
                    flags=part.flags
                ).to_string())

                epub_parts.append(Part(
                    index=part.index,
                    source=part.source,
                    url=get_stored_file_url(self.file_bucket, manifest_path),
                    file_type='application/epub+xml',
                    flags=part.flags
                ).to_string())

        gutenberg_record.record.has_part = epub_parts

    def add_cover(self, gutenberg_record: GutenbergMapping):
        yaml_file = gutenberg_record.yaml_file

        if yaml_file is None:
            return

        for cover_data in yaml_file.get('covers', []):
            if cover_data.get('cover_type') == 'generated': 
                continue

            mime_type, _ = mimetypes.guess_type(cover_data.get('image_path'))
            gutenberg_id = yaml_file.get('identifiers', {}).get('gutenberg')

            file_type = re.search(r'(\.[a-zA-Z0-9]+)$', cover_data.get('image_path')).group(1)
            cover_path = 'covers/gutenberg/{}{}'.format(gutenberg_id, file_type)
            cover_url = get_stored_file_url(self.file_bucket, cover_path)

            gutenberg_record.record.has_part.append(Part(
                index=None,
                source=Source.GUTENBERG.value,
                url=cover_url,
                file_type=mime_type,
                flags=json.dumps(dataclasses.asdict(FileFlags(cover=True)))
            ).to_string())

            cover_root = yaml_file.get('url').replace('ebooks', 'files')
            cover_source_url = f"{cover_root}/{cover_data.get('image_path')}"

            self.rabbitmq_manager.sendMessageToQueue(self.file_queue, self.file_route, get_file_message(cover_source_url, cover_path))
