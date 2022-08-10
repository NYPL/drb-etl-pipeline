import os

from model import Work
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search
from elasticsearch.exceptions import NotFoundError, ConflictError
from main import loadEnvFile


def main():

    '''Deleting ESC works that don't appear in the Postgresql database based on uuid'''

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

    batchSize = 10
    esWorkUUIDS = []
    workUUIDTuples = []
    searchES = Search(index=os.environ['ELASTICSEARCH_INDEX'])

    for work in searchES.query('match_all').scan():
        # Upack the tuples to a flat array
        # Convert the array of ElasticSearch UUIDs and the array of postgresql UUIDs to sets()
        # Take the difference of of the ES set and the postgresql set (https://docs.python.org/3/library/stdtypes.html#frozenset.difference)
        # what you have left should be a set of UUIDs that are in ES but not in psql
            # that's what you should delete!

        esWorkUUIDS.append(work.uuid) # Initialize the array outside of the loop here   
        if len(esWorkUUIDS) >= batchSize:
            for uuid in esWorkUUIDS:
                uuidTuple = dbManager.session.query(Work.uuid) \
                        .filter(Work.uuid == uuid) \
                        .filter(Work.uuid.in_(esWorkUUIDS)).first()
                workUUIDTuples.append(str(uuidTuple[0])) #PSQL work uuids are of type uuid unlike ES work uuids

            setWorkUUIDS = set(esWorkUUIDS) 
            setUUIDTuples = set(workUUIDTuples)

            onlyESWorkUUIDS = setWorkUUIDS.difference(setUUIDTuples) #Set should be empty

            print(onlyESWorkUUIDS)

            try:
                esManager.deleteWorkRecords(onlyESWorkUUIDS)
            except NotFoundError or ValueError or ConflictError:
                if ValueError:
                    print('Empty value')
                elif ConflictError:
                    print('Version number error')
                else:
                    print('Work not indexed, skipping') 
    
    dbManager.closeConnection()


'____________________OLDER CODE BELOW_____________________'


        # if dbManager.session.query(Work) \
        #     .group_by(Work.uuid) \
        #     .filter(Work.uuid == work.uuid) \
        #     .yield_per(batchSize) == None:

        #     try:
        #         ESWork.delete(work.uuid)
        #     except NotFoundError or ValueError or ConflictError:
        #         if ValueError:
        #             print('Empty value')
        #         elif ConflictError:
        #             print('Version number error')
        #         else:
        #             print('Work not indexed, skipping')


if __name__ == '__main__':
    main()