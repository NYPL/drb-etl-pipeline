import os
from collections import deque

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

    batchSize = 1000
    esWorkUUIDS = deque()
    psqlWorkUUIDTuples = deque()
    searchES = Search(index=os.environ['ELASTICSEARCH_INDEX'])

    for work in searchES.query('match_all').scan():
        # Unpack the tuples to a flat array
        # Convert the array of ElasticSearch UUIDs and the array of postgresql UUIDs to sets()
        # Take the difference of of the ES set and the postgresql set (https://docs.python.org/3/library/stdtypes.html#frozenset.difference)
        # what you have left should be a set of UUIDs that are in ES but not in psql
            # that's what you should delete!

        esWorkUUIDS.append(work.uuid) # Initialize the array outside of the loop here  
        if len(esWorkUUIDS) >= batchSize:
            findESOnlyWorks(esWorkUUIDS, psqlWorkUUIDTuples, dbManager, esManager)  
            psqlWorkUUIDTuples = deque()
            esWorkUUIDS = deque()

    findESOnlyWorks(esWorkUUIDS, psqlWorkUUIDTuples, dbManager, esManager) #For any remainder ES works
    
    dbManager.closeConnection()

def findESOnlyWorks(esWorkUUIDS, psqlWorkUUIDTuples, dbManager, esManager):
        for uuid in esWorkUUIDS:
            uuidTuple = dbManager.session.query(Work.uuid) \
                .filter(Work.uuid == uuid) \
                .filter(Work.uuid.in_(esWorkUUIDS)).first()
            if uuidTuple != None:
                psqlWorkUUIDTuples.append(str(uuidTuple[0])) #PSQL work uuids are of type uuid unlike ES work uuids

        setESWorkUUIDS = set(esWorkUUIDS) 
        setPSQLWorkUUIDS = set(psqlWorkUUIDTuples)

        onlyESWorkUUIDS = setESWorkUUIDS.difference(setPSQLWorkUUIDS) #Set should be empty

        try:
            esManager.deleteWorkRecords(onlyESWorkUUIDS)
        except NotFoundError or ValueError or ConflictError:
            if ValueError:
                print('Empty value')
            elif ConflictError:
                print('Version number error')
            else:
                print('Work not indexed, skipping')


if __name__ == '__main__':
    main()