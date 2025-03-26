import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from model import Base
from logger import create_log

logger = create_log(__name__)


class DBManager:
    def __init__(self, user=None, pswd=None, host=None, port=None, db=None):
        super(DBManager, self).__init__()
        self.user = user or DBManager.decryptEnvVar('POSTGRES_USER')
        self.pswd = pswd or DBManager.decryptEnvVar('POSTGRES_PSWD')
        self.host = host or DBManager.decryptEnvVar('POSTGRES_HOST')
        self.port = port or DBManager.decryptEnvVar('POSTGRES_PORT')
        self.db = db or DBManager.decryptEnvVar('POSTGRES_NAME')

        self.engine = None
        self.session = None

    def __enter__(self):
        self.createSession(autoflush=True)
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.close_connection()

    def generateEngine(self):
        try:
            self.engine = create_engine(
                'postgresql://{}:{}@{}:{}/{}'.format(
                    self.user,
                    self.pswd,
                    self.host,
                    self.port,
                    self.db
                )
            )

            return self.engine
        except Exception as e:
            raise e

    def initializeDatabase(self):
        if not inspect(self.engine).has_table('works'):
            Base.metadata.create_all(self.engine)

    def createSession(self, autoflush=False):
        if not self.engine:
            self.generateEngine()
        self.session = sessionmaker(bind=self.engine, autoflush=autoflush)()

    def startSession(self):
        self.session.begin_nested()

    def commitChanges(self, retry=False):
        try:
            self.session.commit()
        except OperationalError as oprErr:
            logger.error('Deadlock in database layer, retry batch')
            logger.debug(oprErr)

            self.rollbackChanges()
            
            if retry is False:
                self.commitChanges(retry=True)
            else:
                logger.warning('Already retried batch, dropping')

    def rollbackChanges(self):
        self.session.rollback()

    def closeConnection(self):
        self.commitChanges()
        self.session.close()
        self.engine.dispose()

    def close_connection(self):
        self.session.close()
        self.engine.dispose()
    
    def bulkSaveObjects(self, objects, onlyChanged=True, retry=False):
        try:
            self.session.bulk_save_objects(objects, update_changed_only=onlyChanged)
            self.session.commit()
            self.session.flush()
        except OperationalError as oprErr:
            logger.error('Deadlock in database layer, retry batch')
            logger.debug(oprErr)

            self.rollbackChanges()
            
            if retry is False:
                self.bulkSaveObjects(objects, onlyChanged=onlyChanged, retry=True)
            else:
                logger.warning('Already retried batch, dropping')

    def windowedQuery(self, table, query, windowSize=100):
        singleEntity = query.is_single_entity
        query = query.add_column(table.date_modified).order_by(table.date_modified)
        query = query.add_column(table.id).order_by(table.id)

        lastID = None
        totalFetched = 0

        while True:
            subQuery = query

            if lastID is not None:
                subQuery = subQuery.filter(table.id > lastID)

            queryChunk = subQuery.limit(windowSize).all()
            totalFetched += windowSize

            if not queryChunk or (self.ingestLimit and totalFetched > self.ingestLimit):
                break

            lastID = queryChunk[-1][-1]

            for row in queryChunk:
                yield row[0] if singleEntity else row[0:-2]

    def deleteRecordsByQuery(self, query):
        try:
            query.delete()
        except OperationalError as oprErr:
            logger.error('Deadlock in database layer, retry batch')
            logger.debug(oprErr)

    @staticmethod
    def decryptEnvVar(envVar):
        encrypted = os.environ.get(envVar, None)
        # TODO Implement Kubernetes encryption
        return encrypted
