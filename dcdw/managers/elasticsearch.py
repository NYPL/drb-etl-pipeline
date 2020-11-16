import os

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import (
    ConnectionError,
    TransportError,
    ConflictError
)
from elasticsearch.helpers import bulk
from elasticsearch_dsl import connections

from model import ESWork


class ElasticsearchManager:
    def __init__(self):
        self.index = os.environ['ES_INDEX']
        self.client = None

    def createElasticConnection(self):
        host = os.environ['ES_HOST']
        port = os.environ['ES_PORT']
        timeout = int(os.environ['ES_TIMEOUT'])
        try:
            self.client = Elasticsearch(
                hosts=[{'host': host, 'port': port}],
                timeout=timeout
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
    