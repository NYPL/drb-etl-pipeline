from managers import ElasticsearchManager
from model import ESWork


def main():
    """Re-indexing works into new ES cluster"""

    esManager = ElasticsearchManager()
    esManager.create_elastic_connection()
    esManager.create_elastic_search_index()
    ESWork.init()
