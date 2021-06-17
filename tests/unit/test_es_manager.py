from elasticsearch.exceptions import ConnectionError
import pytest

from managers import ElasticsearchManager
from model import ESWork


class TestElasticsearchManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {
            'ELASTICSEARCH_INDEX': 'testES',
            'ELASTICSEARCH_HOST': 'host',
            'ELASTICSEARCH_PORT': 'port',
            'ELASTICSEARCH_TIMEOUT': '1000'
        })

        return ElasticsearchManager()

    def test_initializer(self, testInstance):
        assert testInstance.index == 'testES'

    def test_createElasticConnection_success(self, testInstance, mocker):
        mockConnection = mocker.patch('managers.elasticsearch.connections')

        testInstance.createElasticConnection()

        mockConnection.create_connection.assert_called_once_with(
            hosts=['host:port'], timeout=1000, retry_on_timeout=True, max_retries=3
        )

    def test_createELasticSearchIndex_execute(self, testInstance, mocker):
        testIndexCon = mocker.patch('managers.elasticsearch.Index')
        testIndex = mocker.MagicMock()
        testIndexCon.return_value = testIndex
        testIndex.exists.return_value = False
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testIndexCon.assert_called_once_with('testES')
        testIndex.exists.assert_called_once()
        mockInit.assert_called_once()

    def test_createELasticSearchIndex_skip(self, testInstance, mocker):
        testIndexCon = mocker.patch('managers.elasticsearch.Index')
        testIndex = mocker.MagicMock()
        testIndexCon.return_value = testIndex
        testIndex.exists.return_value = True
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testIndexCon.assert_called_once_with('testES')
        testIndex.exists.assert_called_once()
        mockInit.assert_not_called()

    def test_deleteWorkRecords(self, testInstance, mocker):
        mockResp = mocker.MagicMock(name='testQuery')
        mockSearchObj = mocker.MagicMock(name='searchObject')
        mockSearch = mocker.patch('managers.elasticsearch.Search')
        mockSearch.return_value = mockSearchObj
        mockSearchObj.query.return_value = mockResp

        testInstance.deleteWorkRecords(['uuid1', 'uuid2', 'uuid3'])

        assert mockSearch.call_count == 3
        mockSearchObj.query.assert_has_calls([
            mocker.call('match', uuid='uuid1'),
            mocker.call('match', uuid='uuid2'),
            mocker.call('match', uuid='uuid3')
        ])

        assert mockResp.delete.call_count == 3
