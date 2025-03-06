import csv
from datetime import datetime
from io import BytesIO
import gzip
import requests
from typing import Optional

from constants.get_constants import get_constants
from managers import DBManager
from mappings.hathitrust import HathiMapping
from logger import create_log
from ..record_buffer import RecordBuffer
from .. import utils

logger = create_log(__name__)

class HathiTrustProcess():
    HATHI_DATAFILES = 'https://www.hathitrust.org/files/hathifiles/hathi_file_list.json'
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']
    FIELD_SIZE_LIMIT = 131072 * 2 # 131072 is the default size limit

    def __init__(self, *args):
        self.process = args[0]

        self.limit = int(args[4]) if args[4] else None

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager, batch_size=1000)

        self.constants = get_constants()

    def runProcess(self) -> int:
        start_datetime = utils.get_start_datetime(process_type=self.process)

        self.import_from_data_files(start_datetime=start_datetime)

        self.record_buffer.flush()

        logger.info(f'Ingested {self.record_buffer.ingest_count} Hathi Trust records')

        return self.record_buffer.ingest_count
    
    def parse_data_row(self, data_row):
        hathi_record = HathiMapping(data_row, self.constants)
        hathi_record.applyMapping()
        
        self.record_buffer.add(hathi_record.record)

    def import_from_data_files(self, start_datetime: Optional[datetime]=None):
        data_files = self._get_data_files()
        
        for hathi_file in data_files:
            if not hathi_file.get('full') and start_datetime is not None:
                date_format = self.get_hathi_date_format(hathi_file.get('modified'))
                date_modified = datetime.strptime(hathi_file.get('modified'), date_format).replace(tzinfo=None)
                
                if date_modified >= start_datetime:
                    self.import_from_hathi_file(hathi_file.get('url'), start_datetime)
            elif hathi_file.get('full') and start_datetime is None:
                self.import_from_hathi_file(hathi_file.get('url'))
                break

    def _get_data_files(self) -> dict:
        try:
            file_list = requests.get(self.HATHI_DATAFILES, timeout=15)
            file_list.raise_for_status()
        except Exception as e:
            logger.exception('Failed to load Hathi data files')
            raise e

        data_files = file_list.json()

        data_files.sort(
            key=lambda x: datetime.strptime(x['created'], self.get_hathi_date_format(x['created'])).timestamp(),
            reverse=True
        )

        return data_files

    @staticmethod
    def get_hathi_date_format(date_string: str):
        if 'T' in date_string and '-' in date_string:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in date_string:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'

    def import_from_hathi_file(self, hathi_url: str, start_datetime: Optional[datetime]=None):
        try:
            hathi_resp = requests.get(hathi_url, stream=True, timeout=30)
            hathi_resp.raise_for_status()
        except Exception:
            logger.exception(f'Unable to read Hathi Trust file url {hathi_url}')
            return None

        with gzip.open(BytesIO(hathi_resp.content), mode='rt') as hathi_gzip_file:
            hathi_tsv = csv.reader(hathi_gzip_file, delimiter='\t')
            self.read_hathi_file(hathi_tsv, start_datetime)

    def read_hathi_file(self, hathi_tsv, start_datetime: Optional[datetime]=None):
        csv.field_size_limit(self.FIELD_SIZE_LIMIT)

        for _, book in enumerate(hathi_tsv):
            if self.limit and len(self.record_buffer.records) > self.limit:
                break
            
            book_right = (len(book) >= 3 and book[2]) or None
            book_date_updated = (len(book) > 14 and book[14]) or None

            if book_date_updated:
                try:
                    hathi_date_modified = datetime.strptime(book_date_updated, '%Y-%m-%d %H:%M:%S').replace(tzinfo=None)
                except Exception: 
                    hathi_date_modified = None

            if book_right and book_right not in self.HATHI_RIGHTS_SKIPS:
                if not start_datetime or hathi_date_modified >= start_datetime:
                    self.parse_data_row(book)
