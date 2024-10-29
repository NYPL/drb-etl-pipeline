import csv
from datetime import datetime, timedelta, timezone
from io import BytesIO
import gzip
import os
import requests
from requests.exceptions import ReadTimeout, HTTPError

from ..core import CoreProcess
from mappings.hathitrust import HathiMapping
from logger import createLog

logger = createLog(__name__)

class HathiTrustProcess(CoreProcess):
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']

    def __init__(self, *args):
        super(HathiTrustProcess, self).__init__(*args[:4], batchSize=1000)

        self.ingest_limit = int(args[4]) if args[4] else None

        self.generateEngine()
        self.createSession()

    def runProcess(self):
        if self.process == 'daily':
            start_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            self.importRemoteRecords(start_date_time)
        elif self.process == 'complete':
            self.importRemoteRecords(full_or_partial=True)
        elif self.process == 'custom':
            self.importFromSpecificFile(self.customFile)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} Hathi Trust records')

    def importRemoteRecords(self, start_date_time=None, full_or_partial=False):
        self.importFromHathiTrustDataFile(start_date_time, full_dump=full_or_partial)

    def importFromSpecificFile(self, file_path):
        try:
            hathi_file = open(file_path, new_line='')
        except FileNotFoundError:
            raise IOError('Unable to open local CSV file')

        hathiReader = csv.reader(hathi_file, delimiter='\t')
        self.readHathiFile(hathiReader)

    def parseHathiDataRow(self, data_row):
        hathiRec = HathiMapping(data_row, self.statics)
        hathiRec.applyMapping()
        self.addDCDWToUpdateList(hathiRec)


    def importFromHathiTrustDataFile(self, start_date_time=None, full_dump=False):
        try:
            file_list = requests.get(os.environ['HATHI_DATAFILES'], timeout=15)
            file_list.raise_for_status()
        except (ReadTimeout, HTTPError):
            raise IOError('Unable to load data files')

        file_json = file_list.json()

        file_json.sort(
            key=lambda x: datetime.strptime(
                x['created'],
                self.returnHathiDateFormat(x['created'])
            ).timestamp(),
            reverse=True
        )

        for hathi_file in file_json:
            if hathi_file.get('full') == full_dump and hathi_file.get('full') == False:
                hathi_date_format = self.returnHathiDateFormat(hathi_file.get('modified'))
                hathi_date_modified = datetime.strptime(hathi_file.get('modified'), hathi_date_format).replace(tzinfo=None)
                if hathi_date_modified > start_date_time:
                    self.importFromHathiFile(hathi_file.get('url'), start_date_time)
                    break       
            if hathi_file.get('full') == full_dump and hathi_file.get('full') == False:
                self.importFromHathiFile(hathi_file.get('url'), start_date_time)
                break

    @staticmethod
    def returnHathiDateFormat(strDate):
        if 'T' in strDate and '-' in strDate:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in strDate:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'

    def importFromHathiFile(self, hathi_url, start_date_time=None):
        try:
            hathi_resp = requests.get(hathi_url, stream=True, timeout=30)
            hathi_resp.raise_for_status()
        except (ReadTimeout, HTTPError) as e:
            logger.error('Unable to read hathifile url {}'.format(hathi_url))
            logger.debug(e)
            return None

        with gzip.open(BytesIO(hathi_resp.content), mode='rt') as hathiGzip:
            hathi_tsv = csv.reader(hathiGzip, delimiter='\t')
            self.readHathiFile(hathi_tsv, start_date_time)

    def readHathiFile(self, hathi_tsv, start_date_time=None):
        for number_of_books_ingested, book in enumerate(hathi_tsv):
            if self.ingest_limit and number_of_books_ingested > self.ingest_limit:
                break
            
            if len(book) >= 2:
                book_right = book[2]
                if len(book) >= 15:
                    book_date_updated = book[14]
                else:
                    continue
            else:
                continue

            hathi_date_modified = datetime.strptime(book_date_updated, '%Y-%m-%d %H:%M:%S').replace(tzinfo=None)

            if start_date_time:
                if book_right and book_right not in self.HATHI_RIGHTS_SKIPS and hathi_date_modified > start_date_time:
                    self.parseHathiDataRow(book)
            else:
                if book_right and book_right not in self.HATHI_RIGHTS_SKIPS:
                    self.parseHathiDataRow(book)
