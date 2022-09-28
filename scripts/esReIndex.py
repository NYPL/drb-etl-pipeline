import os

from managers import ElasticsearchManager
from main import loadEnvFile

def main():

    '''Re-indexing works into new ES cluster'''

    loadEnvFile('local-qa', fileString='config/{}.yaml')

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()
    esManager.createElasticSearchIndex()


# POST _reindex
# {
#   "source": {
#     "remote": {
#       "host": "http://otherhost:9200",
#       "username": "user",
#       "password": "pass"
#     },
#     "index": "my-index-000001",
#     "query": {
#       "match": {
#         "test": "data"
#       }
#     }
#   },
#   "dest": {
#     "index": "my-new-index-000001"
#   }
# }