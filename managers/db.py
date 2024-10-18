import os
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from model import Base
from logger import createLog

logger = createLog(__name__)


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
