from managers import ElasticsearchManager
from model import ESWork

def main():

    '''Re-indexing works into new ES cluster'''

    esManager = ElasticsearchManager()
    esManager.createElasticConnection()
    esManager.createElasticSearchIndex()
    ESWork.init()