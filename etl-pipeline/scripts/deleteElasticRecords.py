from multiprocessing.sharedctypes import Value
import os
import logging

from model import Work
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search
from elasticsearch.exceptions import NotFoundError, ConflictError


def main():
    """Deleting ESC works that don't appear in the Postgresql database based on uuid"""

    logging.basicConfig(
        filename="deleteESRecords.log", encoding="utf-8", level=logging.INFO
    )

    dbManager = DBManager(
        user=os.environ.get("POSTGRES_USER", None),
        pswd=os.environ.get("POSTGRES_PSWD", None),
        host=os.environ.get("POSTGRES_HOST", None),
        port=os.environ.get("POSTGRES_PORT", None),
        db=os.environ.get("POSTGRES_NAME", None),
    )

    esManager = ElasticsearchManager()
    esManager.create_elastic_connection()

    dbManager.generate_engine()

    dbManager.create_session()

    batchSize = 1000
    esWorkUUIDS = set()
    psqlWorkUUIDS = set()
    searchES = Search(index=os.environ["ELASTICSEARCH_INDEX"])

    for work in searchES.query("match_all").scan():
        # Unpack the tuples to a flat array
        # Convert the array of ElasticSearch UUIDs and the array of postgresql UUIDs to sets()
        # Take the difference of of the ES set and the postgresql set (https://docs.python.org/3/library/stdtypes.html#frozenset.difference)
        # what you have left should be a set of UUIDs that are in ES but not in psql
        # that's what you should delete!

        esWorkUUIDS.add(work.uuid)  # Initialize the array outside of the loop here
        if len(esWorkUUIDS) >= batchSize:
            findESOnlyWorks(esWorkUUIDS, psqlWorkUUIDS, dbManager, esManager)
            psqlWorkUUIDS = set()
            esWorkUUIDS = set()

    findESOnlyWorks(
        esWorkUUIDS, psqlWorkUUIDS, dbManager, esManager
    )  # For any remainder ES works

    dbManager.close_connection()


def findESOnlyWorks(esWorkUUIDS, psqlWorkUUIDS, dbManager, esManager):
    uuidTuple = (
        dbManager.session.query(Work.uuid).filter(Work.uuid.in_(esWorkUUIDS)).all()
    )

    psqlWorkUUIDS.update(
        {str(psqlUUID[0]) for psqlUUID in uuidTuple}
    )  # PSQL work uuids are of type uuid unlike ES work uuids

    onlyESWorkUUIDS = esWorkUUIDS.difference(
        psqlWorkUUIDS
    )  # Set shouldn't be empty when ES work not in PSQL

    logging.info(onlyESWorkUUIDS)

    try:
        esManager.deleteWorkRecords(onlyESWorkUUIDS)
    except NotFoundError or ValueError or ConflictError:
        if ValueError:
            logging.info("Empty value")
        elif ConflictError:
            logging.info("Version number error")
        else:
            logging.info("Work not indexed, skipping")


if __name__ == "__main__":
    main()
