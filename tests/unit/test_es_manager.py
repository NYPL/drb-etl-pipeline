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
        mockClient = mocker.patch('managers.elasticsearch.Elasticsearch')

        testInstance.createElasticConnection()

        mockConnection.create_connection.assert_called_once_with(
            hosts=['host:port'], timeout=1000, retry_on_timeout=True, max_retries=3
        )

        mockClient.assert_called_once_with(
            hosts=['host:port']
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
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_deleteGenerator')
        mockGen.return_value = 'generator'

        testInstance.deleteWorkRecords(['uuid1', 'uuid2', 'uuid3'])

        mockGen.assert_called_once_with(['uuid1', 'uuid2', 'uuid3'])
        mockBulk.assert_called_once_with(
            'mockClient', 'generator', raise_on_error=False
        )

    def test_deleteGenerator(self, testInstance):
        deleteStmts = [out for out in testInstance._deleteGenerator([1, 2, 3])]

        assert deleteStmts == [
            {'_op_type': 'delete', '_index': 'testES', '_id': 1, '_type': 'doc'},
            {'_op_type': 'delete', '_index': 'testES', '_id': 2, '_type': 'doc'},
            {'_op_type': 'delete', '_index': 'testES', '_id': 3, '_type': 'doc'},
        ]

    def test_saveWorkRecords(self, testInstance, mocker):
        testInstance.es = 'mockClient'
        mockBulk = mocker.patch('managers.elasticsearch.bulk')
        mockGen = mocker.patch.object(ElasticsearchManager, '_upsertGenerator')
        mockGen.return_value = 'generator'

        testInstance.saveWorkRecords(['work1', 'work2', 'work3'])

        mockGen.assert_called_once_with(['work1', 'work2', 'work3'])
        mockBulk.assert_called_once_with('mockClient', 'generator')

    def test_upsertGenerator(self, testInstance, mocker):
        mockWork = mocker.MagicMock(uuid=1)
        mockWork.to_dict.return_value = 'mockWork'
        upsertStmts = [out for out in testInstance._upsertGenerator([mockWork])]

        assert upsertStmts == [
            {
                '_op_type': 'update',
                '_index': 'testES',
                '_id': 1,
                '_type': 'doc',
                'doc': 'mockWork',
                'doc_as_upsert': True
            }
        ]
