import os

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections, Search

from model import ESWork


class ElasticsearchManager:
    def __init__(self):
        self.index = os.environ.get('ELASTICSEARCH_INDEX', None)
        self.client = None

    def createElasticConnection(self):
        host = os.environ.get('ELASTICSEARCH_HOST', None)
        port = os.environ.get('ELASTICSEARCH_PORT', None)
        timeout = int(os.environ.get('ELASTICSEARCH_TIMEOUT', 5))
        try:
            self.client = Elasticsearch(
               hosts=['{}:{}'.format(host, port)],
               timeout = timeout,
               retry_on_timeout=True,
               max_retries=3
            )
        except ConnectionError as err:
            raise err

        connections.connections._conns['default'] = self.client

    def createElasticSearchIndex(self):
        if self.client.indices.exists(index=self.index) is False:
            ESWork.init()
        else:
            print('ElasticSearch index {} already exists'.format(self.index))
    
    def bulkSaveElasticSearchRecords(self, records):
        bulk(client=self.client, index=self.index, actions=records)

    def deleteWorkRecords(self, uuids):
        for uuid in uuids:
            workSearch = Search(index=self.index).query('match', uuid=uuid)
            workSearch.delete()
    