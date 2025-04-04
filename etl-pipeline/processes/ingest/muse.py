import csv
import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pymarc import MARCReader
import requests
from requests.exceptions import ReadTimeout, HTTPError

from managers import DBManager, MUSEError, MUSEManager, RabbitMQManager, S3Manager
from mappings.muse import map_muse_record
from model import get_file_message
from logger import create_log
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)


class MUSEProcess():
    MARC_URL = 'https://about.muse.jhu.edu/lib/metadata?format=marc&content=book&include=oa&filename=open_access_books&no_auth=1'
    MARC_CSV_URL = 'https://about.muse.jhu.edu/static/org/local/holdings/muse_book_metadata.csv'
    MUSE_ROOT_URL = 'https://muse.jhu.edu'

    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.create_session()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.s3_manager = S3Manager()

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.create_connection()
        self.rabbitmq_manager.create_or_connect_queue(self.file_queue, self.file_route)

    def runProcess(self):

        if self.params.process_type == 'daily':
            self.importMARCRecords()
        elif self.params.process_type == 'complete':
            self.importMARCRecords(full=True)
        elif self.params.process_type == 'custom':
            self.importMARCRecords(startTimestamp=self.params.ingest_period)
        elif self.params.record_id:
            self.importMARCRecords(recID=self.params.record_id)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} MUSE records')

    def parse_muse_record(self, marc_record):
        record = map_muse_record(marc_record)

        # Use the available source link to create a PDF manifest file and
        # store in S3
        _, muse_link, _, muse_type, _ = list(
            record.has_part[0].split('|')
        )

        muse_manager = MUSEManager(record, muse_link, muse_type)

        muse_manager.parse_muse_page()

        muse_manager.identify_readable_versions()

        muse_manager.add_readable_links()

        if muse_manager.pdfWebpubManifest:
            self.s3_manager.put_object(
                muse_manager.pdfWebpubManifest.toJson().encode('utf-8'),
                muse_manager.s3PDFReadPath,
                muse_manager.s3Bucket
            )

        if muse_manager.epub_url:
            self.rabbitmq_manager.send_message_to_queue(self.file_queue, self.file_route, get_file_message(muse_manager.epub_url, muse_manager.s3_epub_path))

        self.record_buffer.add(record=record)

    def importMARCRecords(self, full=False, startTimestamp=None, recID=None):
        self.downloadRecordUpdates()

        museFile = self.downloadMARCRecords()

        startDateTime = None
        if full is False:
            if not startTimestamp:
                startDateTime = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            else:
                startDateTime = datetime.strptime(startTimestamp, '%Y-%m-%d')

        marcReader = MARCReader(museFile)

        processed_record_count = 0

        for record in marcReader:
            if self.params.limit and processed_record_count >= self.params.limit:
                break

            if (startDateTime or recID) \
                    and self.recordToBeUpdated(record, startDateTime, recID)\
                    is False:
                continue

            try:
                self.parse_muse_record(record)
                processed_record_count += 1
            except MUSEError as e:
                logger.warning('Unable to parse MUSE record')
                logger.debug(e)

    def downloadMARCRecords(self):
        try:
            museResponse = requests.get(MUSEProcess.MARC_URL, stream=True, timeout=30)
            museResponse.raise_for_status()
        except(ReadTimeout, HTTPError) as e:
            logger.error('Unable to load MUSE MARC records')
            logger.debug(e)
            raise Exception('Unable to load Project MUSE MARC file')

        content = bytes()
        for chunk in museResponse.iter_content(1024 * 250):
            content += chunk

        return BytesIO(content)

    def downloadRecordUpdates(self):
        try:
            csvResponse = requests.get(MUSEProcess.MARC_CSV_URL, stream=True, timeout=30)
            csvResponse.raise_for_status()
        except(ReadTimeout, HTTPError) as e:
            logger.error('Unable to load MUSE CSV records')
            logger.debug(e)
            raise Exception('Unable to load Project MUSE CSV file')

        csvReader = csv.reader(
            csvResponse.iter_lines(decode_unicode=True),
            skipinitialspace=True,
        )

        for _ in range(4):
            next(csvReader, None)  # Skip 4 header rows

        self.updateDates = {}
        for row in csvReader:
            try:
                self.updateDates[row[7]] = \
                    datetime.strptime(row[11], '%Y-%m-%d')
            except (IndexError, ValueError):
                logger.warning('Unable to parse MUSE')
                logger.debug(row)

    def recordToBeUpdated(self, record, startDate, recID):
        recordURL = record.get_fields('856')[0]['u']

        updateDate = self.updateDates.get(recordURL[:-1], datetime(1970, 1, 1))

        updateURL = 'https://muse.jhu.edu/book/{}'.format(recID)

        return (updateDate >= startDate) or updateURL == recordURL[:-1]
