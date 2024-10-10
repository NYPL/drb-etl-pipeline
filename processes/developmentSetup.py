import csv
from datetime import datetime
from elasticsearch.exceptions import ConnectionError
import gzip
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
import sqlalchemy as sa
from sqlalchemy.exc import ProgrammingError
from time import sleep

from managers.db import DBManager
from .core import CoreProcess
from logger import createLog
from mappings.hathitrust import HathiMapping
from .oclcClassify import ClassifyProcess
from .oclcCatalog import CatalogProcess
from .sfrCluster import ClusterProcess

logger = createLog(__name__)


class DevelopmentSetupProcess(CoreProcess):
    def __init__(self, *args):
        self.admin_db_manager = DBManager(
            user=os.environ['ADMIN_USER'],
            pswd=os.environ['ADMIN_PSWD'],
            host=os.environ['POSTGRES_HOST'],
            port=os.environ['POSTGRES_PORT'],
            db='postgres'
        )

        self.initialize_db()

        super(DevelopmentSetupProcess, self).__init__(*args[:4])

    def runProcess(self):
        try:
            self.generateEngine()
            self.createSession()

            self.initializeDatabase()

            self.createElasticConnection()
            self.wait_for_elastic_search()
            self.createElasticSearchIndex()

            self.createRabbitConnection()
            self.createOrConnectQueue(os.environ['OCLC_QUEUE'], os.environ['OCLC_ROUTING_KEY'])
            self.createOrConnectQueue(os.environ['FILE_QUEUE'], os.environ['FILE_ROUTING_KEY'])

            self.fetch_hathi_sample_data()

            process_args = ['complete'] + ([None] * 4)

            self.createRedisClient()
            self.clear_cache()

            classify_process = ClassifyProcess(*process_args)
            classify_process.runProcess()

            catalog_process = CatalogProcess(*process_args)
            catalog_process.runProcess(max_attempts=1)
            
            cluster_process = ClusterProcess(*process_args)
            cluster_process.runProcess()
        except Exception:
            logger.exception(f'Failed to run development setup process')

    def initialize_db(self):
        self.admin_db_manager.generateEngine()

        with self.admin_db_manager.engine.connect() as admin_db_connection:
            admin_db_connection.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            self.create_database(admin_db_connection)
            self.create_database_user(admin_db_connection)

        self.admin_db_manager.engine.dispose()

    def create_database(self, db_connection):
        try:
            db_connection.execute(
                sa.text(f"CREATE DATABASE {os.environ['POSTGRES_NAME']}"),
            )
        except ProgrammingError:
            pass
        except Exception as e:
            logger.exception('Failed to create database')
            raise e

    def create_database_user(self, db_connection):
        try:
            db_connection.execute(
                sa.text(
                    f"CREATE USER {os.environ['POSTGRES_USER']} "
                    f"WITH PASSWORD '{os.environ['POSTGRES_PSWD']}'",
                ),
            )
            db_connection.execute(
                sa.text(
                    f"GRANT ALL PRIVILEGES ON DATABASE {os.environ['POSTGRES_NAME']} "
                    f"TO {os.environ['POSTGRES_USER']}",
                ),
            )
        except ProgrammingError:
            pass
        except Exception as e:
            logger.exception('Failed to create database user')
            raise e
        
    def wait_for_elastic_search(self):
        increment = 5
        max_time = 60

        for _ in range(0, max_time, increment):
            try:
                self.es.info()
                break
            except ConnectionError:
                pass
            except Exception as e:
                logger.exception('Failed to wait for elastic search')
                raise e

            sleep(increment)

    def fetch_hathi_sample_data(self):
        self.import_from_hathi_trust_data_file()

        self.saveRecords()
        self.commitChanges()

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
                    hathi_record = HathiMapping(book, self.statics)
                    hathi_record.applyMapping()

                    self.addDCDWToUpdateList(hathi_record)
    
    def map_to_hathi_date_format(self, date: str):
        if 'T' in date and '-' in date:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in date:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'
