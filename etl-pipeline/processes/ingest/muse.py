import csv
import os
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pymarc import MARCReader
import requests
from requests.exceptions import ReadTimeout, HTTPError

from ..core import CoreProcess
from mappings.muse import MUSEMapping
from managers import MUSEError, MUSEManager, RabbitMQManager, S3Manager
from model import get_file_message
from logger import create_log


logger = create_log(__name__)


class MUSEProcess(CoreProcess):
    MARC_URL = 'https://about.muse.jhu.edu/lib/metadata?format=marc&content=book&include=oa&filename=open_access_books&no_auth=1'
    MARC_CSV_URL = 'https://about.muse.jhu.edu/static/org/local/holdings/muse_book_metadata.csv'
    MUSE_ROOT_URL = 'https://muse.jhu.edu'

    def __init__(self, *args):
        super(MUSEProcess, self).__init__(*args[:4])

        self.ingest_limit = int(args[4]) if args[4] else None

        self.generateEngine()
        self.createSession()

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()

        self.fileQueue = os.environ['FILE_QUEUE']
        self.fileRoute = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.fileQueue, self.fileRoute)

    def runProcess(self):
        if self.process == 'daily':
            self.importMARCRecords()
        elif self.process == 'complete':
            self.importMARCRecords(full=True)
        elif self.process == 'custom':
            self.importMARCRecords(startTimestamp=self.ingestPeriod)
        elif self.process == 'single':
            self.importMARCRecords(recID=self.singleRecord)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} MUSE records')

    def parseMuseRecord(self, marcRec):
        museRec = MUSEMapping(marcRec)
        museRec.applyMapping()

        # Use the available source link to create a PDF manifest file and
        # store in S3
        _, museLink, _, museType, _ = list(
            museRec.record.has_part[0].split('|')
        )

        museManager = MUSEManager(museRec, museLink, museType)

        museManager.parseMusePage()

        museManager.identifyReadableVersions()

        museManager.addReadableLinks()

        if museManager.pdfWebpubManifest:
            self.s3_manager.putObjectInBucket(
                museManager.pdfWebpubManifest.toJson().encode('utf-8'),
                museManager.s3PDFReadPath,
                museManager.s3Bucket
            )

        if museManager.epubURL:
            self.rabbitmq_manager.sendMessageToQueue(self.fileQueue, self.fileRoute, get_file_message(museManager.epubURL, museManager.s3EpubPath))

        self.addDCDWToUpdateList(museRec)

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
            if self.ingest_limit and processed_record_count >= self.ingest_limit:
                break

            if (startDateTime or recID) \
                    and self.recordToBeUpdated(record, startDateTime, recID)\
                    is False:
                continue

            try:
                self.parseMuseRecord(record)
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
