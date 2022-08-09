import os

from model import Work, ESWork
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search
from elasticsearch.exceptions import NotFoundError, ConflictError
from main import loadEnvFile


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

    batchSize = 200
    searchES = Search(index=os.environ['ELASTICSEARCH_INDEX'])

    for work in searchES.query('match_all').scan():    
        if dbManager.session.query(Work) \
            .group_by(Work.uuid) \
            .filter(Work.uuid == work.uuid) \
            .yield_per(batchSize) == None:

            try:
                ESWork.delete(work.uuid)
            except NotFoundError or ValueError or ConflictError:
                if ValueError:
                    print('Empty value')
                elif ConflictError:
                    print('Version number error')
                else:
                    print('Work not indexed, skipping')

    dbManager.closeConnection()

if __name__ == '__main__':
    main()