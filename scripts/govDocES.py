import os
from elasticsearch.exceptions import NotFoundError

from model import Work, Edition, ESWork
from main import loadEnvFile
from managers import DBManager, ElasticsearchManager


def main():

    '''Updating is_government_document field of current gov doc works in ES to be the boolean value True'''

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

    for work in dbManager.session.query(Work) \
        .join(Edition) \
        .filter(Edition.measurements != None) \
        .filter(Edition.measurements != []) \
        .filter(Edition.measurements != [{}]).all():
            for dict in work.edition.measurements:
                if dict['type'] == "government_document":
                    if dict['value'] == "1":
                        try:
                            workRec = ESWork.get(work.uuid, index=esManager.index)
                            workRec.is_government_document = True
                            workRec.save()
                            break
                        except NotFoundError:
                            print('Work not indexed, skipping')
                            continue

    dbManager.closeConnection()

if __name__ == '__main__':
    main()