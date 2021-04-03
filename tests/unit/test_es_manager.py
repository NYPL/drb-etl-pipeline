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
        assert testInstance.client == None

    def test_createElasticConnection_success(self, testInstance, mocker):
        mockES = mocker.patch('managers.elasticsearch.Elasticsearch')
        mockClient = mocker.MagicMock()
        mockES.return_value = mockClient

        mockConnection = mocker.patch('managers.elasticsearch.connections')
        mockConnection.connections._conns = {}

        testInstance.createElasticConnection()

        assert testInstance.client == mockClient
        assert mockConnection.connections._conns['default'] == mockClient

        mockES.assert_called_once_with(
            hosts=['host:port'], timeout=1000, retry_on_timeout=True, max_retries=3
        )

    def test_createElasticConnection_error(self, testInstance, mocker):
        mockES = mocker.patch('managers.elasticsearch.Elasticsearch')
        mockClient = mocker.MagicMock()
        mockES.side_effect = ConnectionError

        mockConnection = mocker.patch('managers.elasticsearch.connections')
        mockConnection.connections._conns = {}

        with pytest.raises(ConnectionError):
            testInstance.createElasticConnection()

    def test_createELasticSearchIndex_execute(self, testInstance, mocker):
        testInstance.client = mocker.MagicMock()
        testInstance.client.indices.exists.return_value = False
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testInstance.client.indices.exists.assert_called_once_with(index='testES')
        mockInit.assert_called_once

    def test_createELasticSearchIndex_skip(self, testInstance, mocker):
        testInstance.client = mocker.MagicMock()
        testInstance.client.indices.exists.return_value = True
        
        mockInit = mocker.patch.object(ESWork, 'init')

        testInstance.createElasticSearchIndex()

        testInstance.client.indices.exists.assert_called_once_with(index='testES')
        mockInit.assert_not_called

    def test_bulkSaveElasticSearchRecords(self, testInstance, mocker):
        mockBulk = mocker.patch('managers.elasticsearch.bulk')

        testInstance.bulkSaveElasticSearchRecords([1, 2, 3])

        mockBulk.assert_called_once_with(client=None, index='testES', actions=[1, 2, 3])

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
