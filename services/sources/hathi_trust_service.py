import csv
from datetime import datetime
import gzip
from io import BytesIO
import requests
from typing import Optional, Generator

from constants.get_constants import get_constants
from mappings.hathitrust import HathiMapping
from model import Record
from .source_service import SourceService
from logger import create_log


logger = create_log(__name__)


class HathiTrustService(SourceService):
    HATHI_DATAFILES = 'https://www.hathitrust.org/files/hathifiles/hathi_file_list.json'
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']
    FIELD_SIZE_LIMIT = 131072 * 2 # 131072 is the default size limit

    def __init__(self):
        self.constants = get_constants()
        self.record_count = 0

    def get_records(
        self, 
        full_import: bool = False, 
        start_timestamp: Optional[datetime] = None, 
        offset: int = 0, 
        limit: Optional[int] = None
    ) -> Generator[Record, None, None]:
        data_files = self._get_data_files()
                
        for data_file in data_files:
            if limit and self.record_count >= limit:
                return

            if data_file.get('full') and start_timestamp is None:
                yield from self._get_records_from_data_file(file_url=data_file.get('url'), limit=limit)
            else:
                date_format = self.get_hathi_date_format(date_string=data_file.get('modified'))
                date_modified = datetime.strptime(data_file.get('modified'), date_format).replace(tzinfo=None)
                
                if date_modified >= start_timestamp:
                    yield from self._get_records_from_data_file(file_url=data_file.get('url'), start_datetime=start_timestamp, limit=limit)

    def _get_data_files(self) -> list[dict]:
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

    def _get_records_from_data_file(
        self, 
        file_url: str,
        start_datetime: Optional[datetime]=None,
        limit: Optional[int]=None,
    ) -> Generator[Record, None, None]:
        csv.field_size_limit(self.FIELD_SIZE_LIMIT)

        data_file = self._get_data_from_file_url(file_url)

        if data_file is None:
            return
        
        with gzip.open(BytesIO(data_file), mode='rt') as gzip_file:
            tsv_file = csv.reader(gzip_file, delimiter='\t')

            for data_row in tsv_file:
                if limit and self.record_count > limit:
                    return
                
                if self._is_ingestable(data_row, start_datetime):
                    record_mapping = HathiMapping(data_row, self.constants)
                    record_mapping.applyMapping()

                    yield record_mapping.record
                    self.record_count +=1

    def _get_data_from_file_url(self, file_url: str):
        try:
            data_file_response = requests.get(url=file_url, stream=True, timeout=30)
            data_file_response.raise_for_status()

            return data_file_response.content
        except Exception:
            logger.exception(f'Unable to get data from Hathi Trust file url {file_url}')
            return None
        
    def _is_ingestable(self, data_row, start_datetime: Optional[datetime]) -> bool:
        rights = data_row[2] if len(data_row) > 2 else None
        date_modified = self._get_date_modified(data_row)

        return (
            rights and rights not in self.HATHI_RIGHTS_SKIPS and 
            (not start_datetime or date_modified >= start_datetime)
        )
    
    def _get_date_modified(self, data_row) -> datetime:
        date_modified = data_row[14] if len(data_row) > 14 else None

        try:
            return datetime.strptime(date_modified, '%Y-%m-%d %H:%M:%S') if date_modified else datetime.now()
        except ValueError:
            return datetime.now()
