import csv
from datetime import datetime
import gzip
import os
import requests

from constants.get_constants import get_constants
from ..core import CoreProcess
from logger import createLog
from managers import RedisManager
from mappings.hathitrust import HathiMapping
from processes import CatalogProcess, ClassifyProcess, ClusterProcess

logger = createLog(__name__)


class SeedLocalDataProcess(CoreProcess):
    def __init__(self, *args):
        super(SeedLocalDataProcess, self).__init__(*args[:4])

        self.redis_manager = RedisManager()
        self.constants = get_constants()

    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            self.fetch_hathi_sample_data()

            process_args = ['complete'] + ([None] * 4)


            self.redis_manager.createRedisClient()
            self.redis_manager.clear_cache()

            classify_process = ClassifyProcess(*process_args)
            classify_process.runProcess()

            catalog_process = CatalogProcess(*process_args)
            catalog_process.runProcess(max_attempts=1)
            
            cluster_process = ClusterProcess(*process_args)
            cluster_process.runProcess()
        except Exception as e:
            logger.exception(f'Failed to seed local data')
            raise e

    def fetch_hathi_sample_data(self):
        self.import_from_hathi_trust_data_file()

        self.saveRecords()
        self.commitChanges()

        logger.info(f'Ingested {len(self.records)} Hathi Trust sample records')

    def import_from_hathi_trust_data_file(self):
        hathi_files_response = requests.get(os.environ['HATHI_DATAFILES'])

        if hathi_files_response.status_code != 200:
            raise Exception('Unable to load Hathi Trust data files')

        hathi_files_json = hathi_files_response.json()

        hathi_files_json.sort(
            key=lambda file: datetime.strptime(
                file['created'],
                self.map_to_hathi_date_format(file['created'])
            ).timestamp(),
            reverse=True
        )

        temp_hathi_file = '/tmp/tmp_hathi.txt.gz'
        in_copyright_statuses = { 'ic', 'icus', 'ic-world', 'und' }

        with open(temp_hathi_file, 'wb') as hathi_tsv_file:
            hathi_data_response = requests.get(hathi_files_json[0]['url'])

            hathi_tsv_file.write(hathi_data_response.content)

        with gzip.open(temp_hathi_file, 'rt') as unzipped_tsv_file:
            hathi_tsv_file = csv.reader(unzipped_tsv_file, delimiter='\t')

            for number_of_books_ingested, book in enumerate(hathi_tsv_file):
                if number_of_books_ingested > 500:
                    break

                book_right = book[2]

                if book_right not in in_copyright_statuses:
                    hathi_record = HathiMapping(book, self.constants)
                    hathi_record.applyMapping()

                    self.addDCDWToUpdateList(hathi_record)
    
    def map_to_hathi_date_format(self, date: str):
        if 'T' in date and '-' in date:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in date:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'
