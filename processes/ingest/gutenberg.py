import dataclasses
from datetime import datetime, timedelta, timezone
import json
import mimetypes
import os
import re
from typing import Optional

from constants.get_constants import get_constants
from digital_assets import get_stored_file_url
from managers import DBManager, GutenbergManager, RabbitMQManager
from mappings.gutenberg import GutenbergMapping
from model import get_file_message, FileFlags, Part, Source
from logger import create_log
from .record_buffer import RecordBuffer

logger = create_log(__name__)


class GutenbergProcess():
    GUTENBERG_NAMESPACES = {
        'dcam': 'http://purl.org/dc/dcam/',
        'dcterms': 'http://purl.org/dc/terms/',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'cc': 'http://web.resource.org/cc/',
        'rdfs': 'http://www.w3.org/2000/01/rdf-schema#',
        'pgterms': 'http://www.gutenberg.org/2009/pgterms/'
    }

    def __init__(self, *args):
        self.process = args[0]
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

        self.constants = get_constants()

    def runProcess(self):
        if self.process == 'daily':
            self.import_rdf_records(start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=1))
        elif self.process == 'complete':
            self.import_rdf_records()
        elif self.process == 'custom':
            self.import_rdf_records(start_timestamp=datetime.strptime(self.ingest_period, '%Y-%m-%dT%H:%M:%S'))

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} Gutenberg records')

    def import_rdf_records(self, start_timestamp: Optional[datetime]=None):
        order_direction = 'ASC' if start_timestamp is None else 'DESC'
        order_by = 'CREATED_AT' if start_timestamp is None else 'PUSHED_AT'
        page_size = 100
        current_position = 0

        manager = GutenbergManager(order_direction, order_by, start_timestamp, page_size)

        has_next_page = True

        while has_next_page:
            has_next_page = manager.fetchGithubRepoBatch()

            current_position += page_size
            if current_position <= self.offset: 
                continue

            manager.fetchMetadataFilesForBatch()
            self.process_gutenberg_files(manager.dataFiles)
            manager.resetBatch()

            if current_position >= self.limit: 
                break

    def process_gutenberg_files(self, date_files: tuple):
        for (rdf_file, yaml_file) in date_files:
            gutenberg_record = GutenbergMapping(rdf_file, self.GUTENBERG_NAMESPACES, self.constants)
            gutenberg_record.applyMapping()

            self.store_epubs(gutenberg_record)

            try:
                self.add_cover(gutenberg_record, yaml_file)
            except Exception:
                logger.warning(f'Unable to store cover for {gutenberg_record.record.source_id}')

            self.record_buffer.add(gutenberg_record.record)

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

    def add_cover(self, gutenberg_record: GutenbergMapping, yaml_file):
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
