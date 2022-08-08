import os

from model import Work, ESWork
from main import loadEnvFile
from managers import DBManager, ElasticsearchManager


def main():

    '''Deleting ESC works that don't appear in the Postgresql database as works based on uuid'''

    loadEnvFile('local-qa', fileString='config/{}.yaml')

    dbManager = DBManager(
        user= os.environ.get('POSTGRES_USER', None),
        pswd= os.environ.get('POSTGRES_PSWD', None),
        host= os.environ.get('POSTGRES_HOST', None),
        port= os.environ.get('POSTGRES_PORT', None),
        db= os.environ.get('POSTGRES_NAME', None)
    )

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()

    dbManager.generateEngine()

    dbManager.createSession()

    batchSize = 1000
    for work in esManager.session.query(ESWork) \
        .yield_per(batchSize):       

        if dbManager.session.get(Work, {'uuid': work.uuid}) == None:
            try:
                ESWork.delete(work.uuid)
            except ValueError:
                print('Empty value')

    dbManager.closeConnection()

if __name__ == '__main__':
    main()