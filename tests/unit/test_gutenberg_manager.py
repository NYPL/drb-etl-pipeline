from datetime import datetime
from lxml import etree
import pytest
import requests

from managers.gutenberg import GutenbergManager, GutenbergError
from tests.helper import TestHelpers


class TestGutenbergManager:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):

        return GutenbergManager(None, None, None, None)

    @pytest.fixture
    def testGraphQLRepoResponse(self):
        return {
            'data': {
                'organization': {
                    'repositories': {
                        'pageInfo': {
                            'hasNextPage': True,
                            'endCursor': 'testCursorValue'
                        },
                        'nodes': [
                            {'name': 'repo1', 'pushedAt': '1900-01-01T12:00:00Z'},
                            {'name': 'repo2', 'pushedAt': '1950-01-01T12:00:00Z'},
                            {'name': 'repo3', 'pushedAt': '2000-01-01T12:00:00Z'}
                        ]
                    }
                }
            }
        }

    @pytest.fixture
    def testGraphQLFileResponse(self):
        return {
            'data': {
                'repository': {
                    'rdf': {'text': 'testRDF'},
                    'yaml': {'text': 'testYAML'}
                }
            }
        }

    def test_initializer(self, testInstance):
        assert testInstance.repoOrder == 'DESC'
        assert testInstance.repoSortField == 'PUSHED_AT'
        assert testInstance.startTime is None
        assert testInstance.pageSize == 100
        assert testInstance.githubAPIKey == 'test_github_key'
        assert testInstance.cursor is None
        assert testInstance.repos == []
        assert testInstance.dataFiles == []

    def test_fetchGithubRepoBatch_basic(self, testInstance, testGraphQLRepoResponse, mocker):
        mockQuery = mocker.patch.object(GutenbergManager, 'queryGraphQL')
        mockQuery.return_value = testGraphQLRepoResponse

        continuation = testInstance.fetchGithubRepoBatch()

        assert continuation is True
        assert testInstance.cursor == 'testCursorValue'
        assert testInstance.repos == [
            {'name': 'repo1', 'pushedAt': '1900-01-01T12:00:00Z'},
            {'name': 'repo2', 'pushedAt': '1950-01-01T12:00:00Z'},
            {'name': 'repo3', 'pushedAt': '2000-01-01T12:00:00Z'}
        ]
        assert mockQuery.call_args.args[0].replace(' ', '')\
            ==\
            "{organization(login:\"GITenberg\"){repositories(orderBy:{direction:DESC,field:PUSHED_AT},first:100){pageInfo{endCursor,hasNextPage}nodes{id,name,pushedAt}}}}".replace(' ', '')

    def test_fetchGithubRepoBatch_filter_timestamp(self, testInstance, testGraphQLRepoResponse, mocker):
        mockQuery = mocker.patch.object(GutenbergManager, 'queryGraphQL')
        mockQuery.return_value = testGraphQLRepoResponse

        testInstance.startTime = datetime(1975, 1, 1, 12, 0, 0)
        continuation = testInstance.fetchGithubRepoBatch()

        assert continuation is True
        assert testInstance.cursor == 'testCursorValue'
        assert testInstance.repos == [
            {'name': 'repo3', 'pushedAt': '2000-01-01T12:00:00Z'}
        ]
        assert mockQuery.call_args.args[0].replace(' ', '')\
            ==\
            "{organization(login:\"GITenberg\"){repositories(orderBy:{direction:DESC,field:PUSHED_AT},first:100){pageInfo{endCursor,hasNextPage}nodes{id,name,pushedAt}}}}".replace(' ', '')

    def test_fetchGithubRepoBatch_filter_all(self, testInstance, testGraphQLRepoResponse, mocker):
        mockQuery = mocker.patch.object(GutenbergManager, 'queryGraphQL')
        mockQuery.return_value = testGraphQLRepoResponse

        testInstance.startTime = datetime(2020, 1, 1, 12, 0, 0)
        continuation = testInstance.fetchGithubRepoBatch()

        assert continuation is False
        assert testInstance.cursor == 'testCursorValue'
        assert testInstance.repos == []
        assert mockQuery.call_args.args[0].replace(' ', '')\
            ==\
            "{organization(login:\"GITenberg\"){repositories(orderBy:{direction:DESC,field:PUSHED_AT},first:100){pageInfo{endCursor,hasNextPage}nodes{id,name,pushedAt}}}}".replace(' ', '')

    def test_fetchGithubRepoBatch_with_cursor(self, testInstance, testGraphQLRepoResponse, mocker):
        mockQuery = mocker.patch.object(GutenbergManager, 'queryGraphQL')
        mockQuery.return_value = testGraphQLRepoResponse

        testInstance.cursor = 'initialCursor'
        continuation = testInstance.fetchGithubRepoBatch()

        assert continuation is True
        assert testInstance.cursor == 'testCursorValue'
        assert testInstance.repos == [
            {'name': 'repo1', 'pushedAt': '1900-01-01T12:00:00Z'},
            {'name': 'repo2', 'pushedAt': '1950-01-01T12:00:00Z'},
            {'name': 'repo3', 'pushedAt': '2000-01-01T12:00:00Z'}
        ]
        assert mockQuery.call_args.args[0].replace(' ', '')\
            ==\
            "{organization(login:\"GITenberg\"){repositories(orderBy:{direction:DESC,field:PUSHED_AT},first:100,after:\"initialCursor\"){pageInfo{endCursor,hasNextPage}nodes{id,name,pushedAt}}}}".replace(' ', '')

    def test_fetchMetadataFilesForBatch(self, testInstance, mocker):
        mockFetchFiles = mocker.patch.object(GutenbergManager, 'fetchFilesForRecord')

        testInstance.repos = [{'name': 'test_1'}, {'name': 'test_2'}, {'name': 'other'}]
        testInstance.fetchMetadataFilesForBatch()

        mockFetchFiles.assert_has_calls([
            mocker.call('1', {'name': 'test_1'}), mocker.call('2', {'name': 'test_2'})
        ])

    def test_fetchFilesForRecord(self, testInstance, testGraphQLFileResponse, mocker):
        managerMocks = mocker.patch.multiple(
            GutenbergManager,
            queryGraphQL=mocker.DEFAULT,
            parseRDF=mocker.DEFAULT,
            parseYAML=mocker.DEFAULT
        )
        managerMocks['queryGraphQL'].return_value = testGraphQLFileResponse
        managerMocks['parseRDF'].return_value = 'rdfText'
        managerMocks['parseYAML'].return_value = 'yamlText'

        testInstance.fetchFilesForRecord(1, {'name': 'test'})

        assert testInstance.dataFiles == [('rdfText', 'yamlText')]
        assert  managerMocks['queryGraphQL'].mock_calls[0].args[0].replace(' ', '')\
            ==\
            "{repository(owner:\"GITenberg\",name:\"test\"){rdf:object(expression:\"master:pg1.rdf\"){id,...onBlob{text}}yaml:object(expression:\"master:metadata.yaml\"){id,...onBlob{text}}}}".replace(' ', '')

    def test_fetchFilesForRecord_xmlError(self, testInstance, testGraphQLFileResponse, mocker):
        managerMocks = mocker.patch.multiple(
            GutenbergManager,
            queryGraphQL=mocker.DEFAULT,
            parseRDF=mocker.DEFAULT,
            parseYAML=mocker.DEFAULT
        )
        managerMocks['queryGraphQL'].return_value = testGraphQLFileResponse
        managerMocks['parseRDF'].side_effect = etree.XMLSyntaxError
        managerMocks['parseYAML'].return_value = 'yamlText'

        testInstance.fetchFilesForRecord(1, {'name': 'test'})

        assert testInstance.dataFiles == []

    def test_parseRDF(self, testInstance):
        testXML = testInstance.parseRDF('<test attr="hello">world</test>')

        assert testXML.xpath('//test/@attr')[0] == 'hello'
        assert testXML.xpath('//test/text()')[0] == 'world'

    def test_parseYAML(self, testInstance):
        testYAML = """
            hello: world
            a_list:
                - !test1
                - !test2
        """
        testYAML = testInstance.parseYAML(testYAML)

        assert testYAML['hello'] == 'world'
        assert testYAML['a_list'] == ['test1', 'test2']

    def test_resetBatch(self, testInstance):
        testInstance.repos = [1, 2, 3]
        testInstance.dataFiles = [1, 2, 3]

        testInstance.resetBatch()

        assert testInstance.repos == []
        assert testInstance.dataFiles == []

    def test_queryGraphQL_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 200
        mockResponse.json.return_value = 'testResponse'
        mockPost = mocker.patch.object(requests, 'post')
        mockPost.return_value = mockResponse

        testResponse = testInstance.queryGraphQL('testQuery')

        assert testResponse == 'testResponse'
        mockPost.assert_called_once_with(
            testInstance.githubAPIRoot,
            json={'query': 'testQuery'},
            headers={'Authorization': 'bearer test_github_key'}
        )

    def test_queryGraphQL_failure(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 500
        mockResponse.json.return_value = 'testResponse'
        mockPost = mocker.patch.object(requests, 'post')
        mockPost.return_value = mockResponse

        with pytest.raises(GutenbergError):
            testResponse = testInstance.queryGraphQL('testQuery')

    def test_queryGraphQL_unexpected_error(self, testInstance, mocker):
        mockPost = mocker.patch.object(requests, 'post')
        mockPost.side_effect = Exception

        with pytest.raises(GutenbergError):
            testResponse = testInstance.queryGraphQL('testQuery')

