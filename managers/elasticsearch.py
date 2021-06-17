import os

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search, Index

from model import ESWork


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
            logger.info('ElasticSearch index {} already exists'.format(self.index))
    
    def deleteWorkRecords(self, uuids):
        for uuid in uuids:
            workSearch = Search(index=self.index).query('match', uuid=uuid)
            workSearch.delete()
    