import csv
from datetime import datetime, timedelta, timezone
from io import BytesIO
import gzip
import os
import requests
from requests.exceptions import ReadTimeout, HTTPError

from constants.get_constants import get_constants
from ..core import CoreProcess
from mappings.hathitrust import HathiMapping
from logger import create_log

logger = create_log(__name__)

class HathiTrustProcess(CoreProcess):
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']
    FIELD_SIZE_LIMIT = 131072 * 2 # 131072 is the default size limit

    def __init__(self, *args):
        super(HathiTrustProcess, self).__init__(*args[:4], batchSize=1000)

        self.ingest_limit = int(args[4]) if args[4] else None

        self.generateEngine()
        self.createSession()

        self.constants = get_constants()

    def runProcess(self):
        if self.process == 'daily':
            date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
            self.importFromHathiTrustDataFile(start_date_time=date_time)
        elif self.process == 'complete':
            self.importFromHathiTrustDataFile(full_dump=True)
        elif self.process == 'custom':
            self.importFromSpecificFile(self.customFile)

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} Hathi Trust records')

    def importFromSpecificFile(self, file_path):
        try:
            hathi_file = open(file_path, new_line='')
        except FileNotFoundError:
            raise IOError('Unable to open local CSV file')

        hathiReader = csv.reader(hathi_file, delimiter='\t')
        self.readHathiFile(hathiReader)

    def parseHathiDataRow(self, data_row):
        hathiRec = HathiMapping(data_row, self.constants)
        hathiRec.applyMapping()
        self.addDCDWToUpdateList(hathiRec)


    def importFromHathiTrustDataFile(self, full_dump=False, start_date_time=None):
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
            if not hathi_file.get('full') and not full_dump:
                hathi_date_format = self.returnHathiDateFormat(hathi_file.get('modified'))
                hathi_date_modified = datetime.strptime(hathi_file.get('modified'), hathi_date_format).replace(tzinfo=None)
                if start_date_time and hathi_date_modified >= start_date_time:
                    self.importFromHathiFile(hathi_file.get('url'), start_date_time)      
            elif hathi_file.get('full') and full_dump:
                self.importFromHathiFile(hathi_file.get('url'))
                break
            else:
                continue

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
        except Exception:
            logger.exception(f'Unable to read Hathi Trust file url {hathi_url}')
            return None

        with gzip.open(BytesIO(hathi_resp.content), mode='rt') as hathiGzip:
            hathi_tsv = csv.reader(hathiGzip, delimiter='\t')
            self.readHathiFile(hathi_tsv, start_date_time)

    def readHathiFile(self, hathi_tsv, start_date_time=None):
        csv.field_size_limit(self.FIELD_SIZE_LIMIT)

        for number_of_books_ingested, book in enumerate(hathi_tsv):
            if self.ingest_limit and number_of_books_ingested > self.ingest_limit:
                break
            
            book_right = (len(book) >= 3 and book[2]) or None
            book_date_updated = (len(book) > 14 and book[14]) or None

            if book_date_updated:
                try:
                    hathi_date_modified = datetime.strptime(book_date_updated, '%Y-%m-%d %H:%M:%S').replace(tzinfo=None)
                except Exception: 
                    hathi_date_modified = None

            if book_right and book_right not in self.HATHI_RIGHTS_SKIPS:
                if not start_date_time or hathi_date_modified >= start_date_time:
                    self.parseHathiDataRow(book)
