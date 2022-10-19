from managers import ElasticsearchManager
from model import ESWork

def main():

    '''Re-indexing works into new ES cluster'''

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()
    esManager.createElasticSearchIndex()
    ESWork.init()


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