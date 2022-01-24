import os

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConflictError
from elasticsearch.helpers import bulk
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

        self.es = Elasticsearch(
            hosts=['{}:{}'.format(host, port)]
        )

    def createElasticSearchIndex(self):
        esIndex = Index(self.index)
        if esIndex.exists() is False:
            ESWork.init()
        else:
            logger.info(
                'ElasticSearch index {} already exists'.format(self.index)
            )

    def saveWorkRecords(self, works):
        print('Saving ES Work Records')

        def upsertGen():
            for work in works:
                yield {
                    '_op_type': 'update',
                    '_index': self.index,
                    '_id': work.uuid,
                    '_type': 'doc',
                    'doc': work.to_dict(),
                    'doc_as_upsert': True
                }

        saveRes = bulk(self.es, upsertGen())
        print(saveRes)

    def deleteWorkRecords(self, uuids):
        print('Deleting ES Work Records')
        
        def deleteGen():
            for uuid in uuids:
                yield {
                    '_op_type': 'delete',
                    '_index': self.index,
                    '_id': uuid,
                    '_type': 'doc'
                }

        deleteRes = bulk(self.es, deleteGen(), raise_on_error=False)
        print(deleteRes)
