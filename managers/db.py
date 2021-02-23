import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from model import Base


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
        if not self.engine.dialect.has_table(self.engine, 'works'):
            Base.metadata.create_all(self.engine)

    def createSession(self, autoflush=False):
        if not self.engine:
            self.generateEngine()
        self.session = sessionmaker(bind=self.engine, autoflush=autoflush)()

    def startSession(self):
        self.session.begin_nested()

    def commitChanges(self):
        self.session.commit()

    def rollbackChanges(self):
        self.session.rollback()

    def closeConnection(self):
        self.commitChanges()
        self.session.close()
        self.engine.dispose()
    
    def bulkSaveObjects(self, objects, onlyChanged=True):
        self.session.bulk_save_objects(objects, update_changed_only=onlyChanged)
        self.session.commit()
        self.session.flush()

    @staticmethod
    def decryptEnvVar(envVar):
        encrypted = os.environ.get(envVar, None)
        # TODO Implement Kubernetes encryption
        return encrypted
