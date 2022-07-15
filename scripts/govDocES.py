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

            break_out_flag = False
            
            for edition in work.editions:
                for measurement in edition.measurements:
                    if measurement['type'] == "government_document":
                        if measurement['value'] == "1":
                            try:
                                workRec = ESWork.get(work.uuid, index=esManager.index)
                                workRec.is_government_document = True
                                workRec.save()
                                break_out_flag = True
                                break
                            except NotFoundError:
                                print('Work not indexed, skipping')
                                continue
                if break_out_flag:
                    break

    dbManager.closeConnection()

if __name__ == '__main__':
    main()