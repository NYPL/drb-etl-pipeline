import csv
from datetime import datetime
import gzip
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import requests
from sqlalchemy.exc import ProgrammingError

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
        # Setup database if necessary
        self.generateEngine()
        self.createSession()
        self.initializeDatabase()

        # Setup ElasticSearch index if necessary
        self.createElasticConnection()
        self.createElasticSearchIndex()

        # Create rabbit queues
        self.createRabbitConnection()
        self.createOrConnectQueue(os.environ['OCLC_QUEUE'], os.environ['OCLC_ROUTING_KEY'])
        self.createOrConnectQueue(os.environ['FILE_QUEUE'], os.environ['FILE_ROUTING_KEY'])

        # Populate with set of sample data from sources
        self.fetchHathiSampleData()

        procArgs = ['complete'] + ([None] * 4)
        # FRBRize the fetched data
        classifyProc = ClassifyProcess(*procArgs)
        classifyProc.runProcess()

        catalogProc = CatalogProcess(*procArgs)
        catalogProc.runProcess()

        # Group the fetched data
        clusterProc = ClusterProcess(*procArgs)
        clusterProc.runProcess()
        
    def initializeDB(self):
        self.adminDBConnection.generateEngine()
        with self.adminDBConnection.engine.connect() as conn:
            conn.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            try:
                conn.execute('CREATE DATABASE {}'.format(os.environ['POSTGRES_NAME']))
            except ProgrammingError:
                pass

            try:
                conn.execute('CREATE USER {} WITH PASSWORD \'{}\''.format(
                    os.environ['POSTGRES_USER'], os.environ['POSTGRES_PSWD']
                ))
                conn.execute('GRANT ALL PRIVILEGES ON DATABASE {} TO {}'.format(
                    os.environ['POSTGRES_NAME'], os.environ['POSTGRES_USER'])
                )
            except ProgrammingError:
                pass

        self.adminDBConnection.engine.dispose()

    def fetchHathiSampleData(self):
        self.importFromHathiTrustDataFile()
        self.saveRecords()
        self.commitChanges()

    def importFromHathiTrustDataFile(self):
        fileList = requests.get(os.environ['HATHI_DATAFILES'])
        if fileList.status_code != 200:
            raise IOError('Unable to load data files')

        fileJSON = fileList.json()

        fileJSON.sort(
            key=lambda x: datetime.strptime(
                x['created'],
                '%Y-%m-%dT%H:%M:%S-%f'
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

