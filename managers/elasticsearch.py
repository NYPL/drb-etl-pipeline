import os

from elasticsearch.exceptions import ConflictError
from elasticsearch_dsl import connections, Search, Index

from model import ESWork
from logger import createLog

logger = createLog(__name__)


class ElasticsearchManager:
    def __init__(self):
        self.index = os.environ.get('ELASTICSEARCH_INDEX', None)

    def createElasticConnection(self):
        host = os.environ.get('ELASTICSEARCH_HOST', None)
        port = os.environ.get('ELASTICSEARCH_PORT', None)
        timeout = int(os.environ.get('ELASTICSEARCH_TIMEOUT', 5))

        connections.create_connection(
            hosts=['{}:{}'.format(host, port)],
            timeout=timeout,
            retry_on_timeout=True,
            max_retries=3
        )

    def createElasticSearchIndex(self):
        esIndex = Index(self.index)
        if esIndex.exists() is False:
            ESWork.init()
        else:
            logger.info(
                'ElasticSearch index {} already exists'.format(self.index)
            )

    def deleteWorkRecords(self, uuids):
        for uuid in uuids:
            retries = 0

            while True:
                try:
                    logger.debug('Deleting work {}'.format(uuid))

                    workSearch = Search(index=self.index)\
                        .query('match', uuid=uuid)

                    workSearch.params(
                        refresh=True,
                        wait_for_active_shards='all'
                    )

                    workSearch.delete()

                    break
                except ConflictError as e:
                    if retries >= 2:
                        logger.error('Unable to delete work {}'.format(uuid))
                        raise e

                    logger.warning(
                        'Unable to delete work {}. Retrying'.format(uuid)
                    )

                    retries += 1
