from flask import Flask
import pytest

from api.blueprints.drbSearch import standardQuery
from api.utils import APIUtils
from api.elastic import ElasticClientError

class TestSearchBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            extractParamPairs=mocker.DEFAULT,
            formatAggregationResult=mocker.DEFAULT,
            formatPagingOptions=mocker.DEFAULT,
            formatWorkOutput=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT
        )

    @pytest.fixture
    def FakeHit(self, mocker):
        class FakeHit:
            def __init__(self, uuid, edition_ids):
                self.uuid = uuid
                editions = []
                for edition_id in edition_ids:
                    ed = mocker.MagicMock()
                    ed.edition_id = edition_id
                    editions.append(ed)
                mockMeta = mocker.MagicMock()
                mockMeta.inner_hits.editions.hits = editions
                self.meta = mockMeta

        return FakeHit

    @pytest.fixture
    def mockHits(self, FakeHit, mocker):
        class FakeHits:
            def __init__(self):
                self.total = 5
                self.hits = [
                    FakeHit('uuid1', ['ed1', 'ed2']), FakeHit('uuid2', ['ed3']),
                    FakeHit('uuid3', ['ed4', 'ed5', 'ed6']),
                    FakeHit('uuid4', ['ed7']), FakeHit('uuid5', ['ed8'])
                ]

            def __iter__(self):
                for h in self.hits:
                    yield h
        
        return FakeHits()
    
    def test_standardQuery(self, mockUtils, mockHits, mocker):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['REDIS_CLIENT'] = 'testRedisClient'

        mockES = mocker.MagicMock()
        mockESClient = mocker.patch('api.blueprints.drbSearch.ElasticClient')
        mockESClient.return_value = mockES

        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbSearch.DBClient')
        mockDBClient.return_value = mockDB

        queryParams = {'query': ['q1', 'q2'], 'sort': ['s1'], 'size': [5]}
        mockUtils['normalizeQueryParams'].return_value = queryParams
            
        mockUtils['extractParamPairs'].side_effect = [
            ['testQueryTerms'], ['testSortTerms'], [('format', 'html')], ['testShowAll']
        ]
        mockUtils['formatAggregationResult'].return_value = 'testFacets'
        mockUtils['formatPagingOptions'].return_value = 'testPaging'

        mockResponse = mocker.MagicMock()
        mockResponse.hits = mockHits
        mockAgg = mocker.MagicMock()
        mockAgg.to_dict.return_value = {'aggs': []}
        mockResponse.aggregations = mockAgg
        mockES.searchQuery.return_value = mockResponse

        mockDB.fetchSearchedWorks.return_value = ['work1', 'work2', 'work3', 'work4', 'work5']

        mockUtils['formatWorkOutput'].return_value = 'testWorks'

        mockUtils['formatResponseObject'].return_value = 'mockAPIResponse'

        with flaskApp.test_request_context('/?testing=true'):
            testAPIResponse = standardQuery()

            assert testAPIResponse == 'mockAPIResponse'
            mockESClient.assert_called_once_with('testRedisClient')
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once
            mockUtils['extractParamPairs'].assert_has_calls([
                mocker.call('query', queryParams),
                mocker.call('sort', queryParams),
                mocker.call('filter', queryParams),
                mocker.call('showAll', queryParams)
            ])
            mockES.searchQuery.assert_called_once_with(
                {'query': ['testQueryTerms'], 'sort': ['testSortTerms'], 'filter': [('format', 'html'), 'testShowAll']},
                page=0, perPage=5
            )
            testResultIds = [
                ('uuid1', ['ed1', 'ed2']), ('uuid2', ['ed3']),
                ('uuid3', ['ed4', 'ed5', 'ed6']), ('uuid4', ['ed7']), ('uuid5', ['ed8'])
            ]
            mockDB.fetchSearchedWorks.assert_called_once_with(testResultIds)
            mockUtils['formatAggregationResult'].assert_called_once_with({'aggs': []})
            mockUtils['formatPagingOptions'].assert_called_once_with(1, 5, 5)
            mockUtils['formatWorkOutput'].assert_called_once_with(
                ['work1', 'work2', 'work3', 'work4', 'work5'],
                testResultIds,
                formats=['text/html']
            )

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'searchResponse',
                {'totalWorks': 5, 'works': 'testWorks', 'paging': 'testPaging', 'facets': 'testFacets'}
            )

    def test_standardQuery_elastic_error(self, mockUtils, mocker):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['REDIS_CLIENT'] = 'testRedisClient'

        mockES = mocker.MagicMock()
        mockESClient = mocker.patch('api.blueprints.drbSearch.ElasticClient')
        mockESClient.return_value = mockES

        mocker.patch('api.blueprints.drbSearch.DBClient')

        queryParams = {'query': ['q1', 'q2'], 'sort': ['s1'], 'size': [5]}
        mockUtils['normalizeQueryParams'].return_value = queryParams
            
        mockUtils['extractParamPairs'].side_effect = [
            ['testQueryTerms'], ['testSortTerms'], ['testFilterTerms'], ['testShowAll']
        ]

        mockUtils['formatResponseObject'].return_value = 'mockAPIResponse'

        mockES.searchQuery.side_effect = ElasticClientError('Test Exception')

        with flaskApp.test_request_context('/?testing=true'):
            testAPIResponse = standardQuery()

            assert testAPIResponse == 'mockAPIResponse'

            mockUtils['formatResponseObject'].assert_called_once_with(
                400, 'searchResponse', {'message': 'Test Exception'}
            )
