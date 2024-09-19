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
import alembic.config

from managers.db import DBManager
from .core import CoreProcess
from mappings.hathitrust import HathiMapping
from .oclcClassify import ClassifyProcess
from .oclcCatalog import CatalogProcess
from .sfrCluster import ClusterProcess

class DevelopmentSetupProcess(CoreProcess):
    def __init__(self, *args):
        self.adminDBConnection = DBManager(
            user=os.environ['ADMIN_USER'],
            pswd=os.environ['ADMIN_PSWD'],
            host=os.environ['POSTGRES_HOST'],
            port=os.environ['POSTGRES_PORT'],
            db='postgres'
        )
        self.initializeDB()

        super(DevelopmentSetupProcess, self).__init__(*args[:4])

    def runProcess(self):
        self.generateEngine()
        self.createSession()

        self.initializeDatabase()
        self.runDBMigration()

        self.createElasticConnection()
        self.waitForElasticSearch()
        self.createElasticSearchIndex()

        self.createRabbitConnection()
        self.createOrConnectQueue(os.environ['OCLC_QUEUE'], os.environ['OCLC_ROUTING_KEY'])
        self.createOrConnectQueue(os.environ['FILE_QUEUE'], os.environ['FILE_ROUTING_KEY'])

        self.fetchHathiSampleData()

        procArgs = ['complete'] + ([None] * 4)

        self.createRedisClient()
        self.clear_cache()

        classifyProc = ClassifyProcess(*procArgs)
        classifyProc.runProcess()

        catalogProc = CatalogProcess(*procArgs)
        catalogProc.runProcess(max_attempts=1)
        
        clusterProc = ClusterProcess(*procArgs)
        clusterProc.runProcess()

    def runDBMigration(self):
        try:
            alembicArgs = [
                '--raiseerr',
                'upgrade', 'head',
            ]
            alembic.config.main(argv=alembicArgs)
        except Exception as e:
            print(f'Failed to run database migration due to: {e}')

    def initializeDB(self):
        self.adminDBConnection.generateEngine()
        with self.adminDBConnection.engine.connect() as conn:
            conn.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            try:
                conn.execute(
                    sa.text(f"CREATE DATABASE {os.environ['POSTGRES_NAME']}"),
                )
            except ProgrammingError:
                pass

            try:
                conn.execute(
                    sa.text(
                        f"CREATE USER {os.environ['POSTGRES_USER']} "
                        f"WITH PASSWORD '{os.environ['POSTGRES_PSWD']}'",
                    ),
                )
                conn.execute(
                    sa.text(
                        f"GRANT ALL PRIVILEGES ON DATABASE {os.environ['POSTGRES_NAME']} "
                        f"TO {os.environ['POSTGRES_USER']}",
                    ),
                )
            except ProgrammingError:
                pass

        self.adminDBConnection.engine.dispose()

    def fetchHathiSampleData(self):
        self.importFromHathiTrustDataFile()
        self.saveRecords()
        self.commitChanges()

    def waitForElasticSearch(self):
        increment = 5
        totalTime = 0
        while True and totalTime < 60:
            try:
                self.es.info()
                break
            except ConnectionError:
                pass

            totalTime += increment
            sleep(increment)

    @staticmethod
    def returnHathiDateFormat(strDate):
        if 'T' in strDate and '-' in strDate:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in strDate:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'

    def importFromHathiTrustDataFile(self):
        fileList = requests.get(os.environ['HATHI_DATAFILES'])
        if fileList.status_code != 200:
            raise IOError('Unable to load data files')

        fileJSON = fileList.json()

        fileJSON.sort(
            key=lambda x: datetime.strptime(
                x['created'],
                self.returnHathiDateFormat(x['created'])
            ).timestamp(),
            reverse=True
        )

        with open('/tmp/tmp_hathi.txt.gz', 'wb') as hathiTSV:
            hathiReq = requests.get(fileJSON[0]['url'])
            hathiTSV.write(hathiReq.content)

        with gzip.open('/tmp/tmp_hathi.txt.gz', 'rt') as unzipTSV:
            hathiTSV = csv.reader(unzipTSV, delimiter='\t')
            for i, row in enumerate(hathiTSV):
                if row[2] not in ['ic', 'icus', 'ic-world', 'und']:
                    hathiRec = HathiMapping(row, self.statics)
                    hathiRec.applyMapping()
                    self.addDCDWToUpdateList(hathiRec)

                if i >= 500:
                    break
