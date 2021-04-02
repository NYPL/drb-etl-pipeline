import pytest

from tests.helper import TestHelpers
from api.elastic import ElasticClient


class TestElasticClient:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class MockElasticClient(ElasticClient):
            def __init__(self):
                self.client = mocker.MagicMock()

        return MockElasticClient()

    @pytest.fixture
    def mockSearch(self, mocker):
        mockSearch = mocker.MagicMock(name='mockSearch')
        mockSearch.query.return_value = [mockSearch]
        mockSearch.execute.return_value = 'searchResult'

        return mockSearch

    @pytest.fixture
    def searchMocks(self, mockSearch, mocker):
        return mocker.patch.multiple(
            ElasticClient,
            getFromSize=mocker.DEFAULT,
            createSearch=mocker.DEFAULT,
            titleQuery=mocker.DEFAULT,
            authorQuery=mocker.DEFAULT,
            subjectQuery=mocker.DEFAULT,
            authorityQuery=mocker.DEFAULT,
            addFilterClausesAndAggregations=mocker.DEFAULT,
            addSortClause=mocker.DEFAULT
        )

    def test_createSearch(self, testInstance, mocker):
        mockSearch = mocker.patch('api.elastic.Search')
        mockSearch.return_value = 'searchClient'

        searchClient = testInstance.createSearch()

        assert searchClient == 'searchClient'
        mockSearch.assert_called_once_with(using=testInstance.client, index='test_es_index')

    def test_searchQuery_keyword_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['authorQuery'].return_value = 'authorQuery'
        searchMocks['subjectQuery'].return_value = 'subjectQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['testQuery1', 'testQuery2', 'searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('keyword', 'test'), (None, 'test2')],
            'sort': ['sort'],
            'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_has_calls([
            mocker.call('bool', should=['titleQuery', 'authorQuery', 'subjectQuery']),
            mocker.call('bool', should=['titleQuery', 'authorQuery', 'subjectQuery']),
            mocker.call('bool', must=['testQuery1', 'testQuery2'])
        ])
        searchMocks['titleQuery'].assert_has_calls([mocker.call('test'), mocker.call('test2')])
        searchMocks['authorQuery'].assert_has_calls([mocker.call('test'), mocker.call('test2')])
        searchMocks['subjectQuery'].assert_has_calls([mocker.call('test'), mocker.call('test2')])
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once()

    def test_searchQuery_title_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('title', 'test'), ], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['titleQuery'])
        searchMocks['titleQuery'].assert_called_once_with('test')
        searchMocks['authorQuery'].assert_not_called
        searchMocks['subjectQuery'].assert_not_called
        searchMocks['authorityQuery'].assert_not_called

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once

    def test_searchQuery_author_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorQuery'].return_value = 'authorQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('author', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['authorQuery'])
        searchMocks['titleQuery'].assert_not_called
        searchMocks['authorQuery'].assert_called_once_with('test')
        searchMocks['subjectQuery'].assert_not_called
        searchMocks['authorityQuery'].assert_not_called

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once

    def test_searchQuery_subject_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['subjectQuery'].return_value = 'subjectQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('subject', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['subjectQuery'])
        searchMocks['titleQuery'].assert_not_called
        searchMocks['authorQuery'].assert_not_called
        searchMocks['subjectQuery'].assert_called_once_with('test')
        searchMocks['authorityQuery'].assert_not_called

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once

    def test_searchQuery_authority_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorityQuery'].return_value = 'authorityQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('viaf', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['authorityQuery'])
        searchMocks['titleQuery'].assert_not_called
        searchMocks['authorQuery'].assert_not_called
        searchMocks['subjectQuery'].assert_not_called
        searchMocks['authorityQuery'].assert_called_once_with('viaf', 'test')

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once

    def test_searchQuery_generic_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['genericQuery', 'searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('other', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_has_calls([
            mocker.call('match', other='test'),
            mocker.call('bool', must=['genericQuery'])
        ])
        searchMocks['titleQuery'].assert_not_called
        searchMocks['authorQuery'].assert_not_called
        searchMocks['subjectQuery'].assert_not_called
        searchMocks['authorityQuery'].assert_not_called

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

        mockSearch.execute.assert_called_once

    def test_searchQuery_multi_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorityQuery'].return_value = 'authorityQuery'
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['addFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('title', 'testTitle'), ('lcnaf', 'test')],
            'sort': ['sort'],
            'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['titleQuery', 'authorityQuery'])

        searchMocks['titleQuery'].assert_called_once_with('testTitle')
        searchMocks['authorQuery'].assert_not_called
        searchMocks['subjectQuery'].assert_not_called
        searchMocks['authorityQuery'].assert_called_once_with('lcnaf', 'test')

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['addFilterClausesAndAggregations'].assert_called_once_with([mockSearch], ['filter'], 3)
        searchMocks['addSortClause'].assert_called_once_with(mockSearch, ['sort'])

    def test_titleQuery(self):
        testQueryES = ElasticClient.titleQuery('testTitle')
        testQuery = testQueryES.to_dict()

        assert testQuery['bool']['should'][0]['query_string']['query'] == 'testTitle'
        assert testQuery['bool']['should'][0]['query_string']['fields'] == ['title', 'alt_titles']
        assert testQuery['bool']['should'][1]['nested']['path'] == 'editions'
        assert testQuery['bool']['should'][1]['nested']['query']['query_string']['query'] == 'testTitle'
        assert testQuery['bool']['should'][1]['nested']['query']['query_string']['fields'] == ['editions.title']

    def test_authorQuery(self):
        testQueryES = ElasticClient.authorQuery('testAuthor')
        testQuery = testQueryES.to_dict()

        assert testQuery['bool']['should'][0]['nested']['path'] == 'agents'
        assert testQuery['bool']['should'][0]['nested']['query']['bool']['must'][0]['query_string']['query'] == 'testAuthor'
        assert testQuery['bool']['should'][0]['nested']['query']['bool']['must'][0]['query_string']['fields'] == ['agents.name']
        assert testQuery['bool']['should'][0]['nested']['query']['bool']['must_not'][0]['terms']['agents.roles'] == ElasticClient.ROLE_BLOCKLIST
        assert testQuery['bool']['should'][1]['nested']['path'] == 'editions.agents'
        assert testQuery['bool']['should'][1]['nested']['query']['bool']['must'][0]['query_string']['query'] == 'testAuthor'
        assert testQuery['bool']['should'][1]['nested']['query']['bool']['must'][0]['query_string']['fields'] == ['editions.agents.name']
        assert testQuery['bool']['should'][1]['nested']['query']['bool']['must_not'][0]['terms']['editions.agents.roles'] == ElasticClient.ROLE_BLOCKLIST

    def test_authorityQuery(self):
        testQueryES = ElasticClient.authorityQuery('testAuth', 'testID')
        testQuery = testQueryES.to_dict()

        assert testQuery['bool']['should'][0]['nested']['path'] == 'agents'
        assert testQuery['bool']['should'][0]['nested']['query']['term']['agents.testAuth'] == 'testID'
        assert testQuery['bool']['should'][1]['nested']['path'] == 'editions.agents'
        assert testQuery['bool']['should'][1]['nested']['query']['term']['editions.agents.testAuth'] == 'testID'

    def test_subjectQuery(self):
        testQueryES = ElasticClient.subjectQuery('testSubject')
        testQuery = testQueryES.to_dict()

        assert testQuery['nested']['path'] == 'subjects'
        assert testQuery['nested']['query']['query_string']['query'] == 'testSubject'
        assert testQuery['nested']['query']['query_string']['fields'] == ['subjects.heading']

    def test_getFromSize(self):
        startPosition, endPosition = ElasticClient.getFromSize(3, 15)

        assert startPosition == 45
        assert endPosition == 60

    def test_getFromSize_initial(self):
        startPosition, endPosition = ElasticClient.getFromSize(0, 20)
        assert startPosition == 0
        assert endPosition == 20
    
    def test_addSortClause_title_w_direction(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        sortResult = ElasticClient.addSortClause(mockQuery, [('title', 'DESC')])

        assert sortResult == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'sort_title': {'order': 'DESC'}}, {'uuid': 'asc'}
        )
    
    def test_addSortClause_title_wo_direction(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        sortResult = ElasticClient.addSortClause(mockQuery, [('title', None)])

        assert sortResult == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'sort_title': {'order': 'ASC'}}, {'uuid': 'asc'}

        )
    
    def test_addSortClause_author(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        sortResult = ElasticClient.addSortClause(mockQuery, [('author', 'ASC')])

        assert sortResult == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'agents.sort_name': {'order': 'ASC', 'nested': {'path': 'agents', 'filter': {'terms': {'agents.roles': ['author']}}, 'max_children': 1}}},
            {'uuid': 'asc'}
        )
    
    def test_addSortClause_date(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        sortResult = ElasticClient.addSortClause(mockQuery, [('date', 'DESC')])

        assert sortResult == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'publication_date': {'order': 'DESC', 'nested': {'path': 'editions'}}},
            {'uuid': 'asc'}
        )
    
    def test_addSortClause_root_sort_only(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        sortResult = ElasticClient.addSortClause(mockQuery, [])

        assert sortResult == 'sortQuery'
        mockQuery.sort.assert_called_once_with({'uuid': 'asc'})

    def test_addFilterClausesAndAggregations_default(self, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.return_value = 'formatFilter'
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.return_value = 'formatAggregation'

        mockSearch = mocker.MagicMock()

        mockApply = mocker.patch.object(ElasticClient, 'applyFilters')
        mockApply.return_value = mockSearch
        mockApplyAggs = mocker.patch.object(ElasticClient, 'applyAggregations')

        ElasticClient.addFilterClausesAndAggregations(mockSearch, [], 1)

        mockQuery.assert_called_once_with('exists', field='editions.formats')
        mockAgg.assert_called_once_with('filter', exists={'field': 'editions.formats'})

        mockApply.assert_called_once_with(mockSearch, [], ['formatFilter'], size=1)
        mockApplyAggs.assert_called_once_with(mockSearch, ['formatAggregation'])

    def test_addFilterClausesAndAggregations_w_date(self, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['dateFilter', 'formatFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['dateAggregation', 'formatAggregation']

        mockSearch = mocker.MagicMock()

        mockGenerateRange = mocker.patch.object(ElasticClient, 'generateDateRange')
        mockGenerateRange.return_value = 'testRange'
        mockApply = mocker.patch.object(ElasticClient, 'applyFilters')
        mockApply.return_value = mockSearch
        mockApplyAggs = mocker.patch.object(ElasticClient, 'applyAggregations')

        ElasticClient.addFilterClausesAndAggregations(mockSearch, [('startYear', 1900)], 1)

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
            mocker.call('range', **{'editions.publication_date': 'testRange'})
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
            mocker.call('filter', range={'editions.publication_date': 'testRange'})
        ])

        mockApply.assert_called_once_with(mockSearch, [], ['formatFilter', 'dateFilter'], size=1)
        mockApplyAggs.assert_called_once_with(mockSearch, ['formatAggregation', 'dateAggregation'])

    def test_addFilterClausesAndAggregations_w_format(self, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['displayFilter', 'formatFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['displayAggregation', 'formatAggregation']

        mockSearch = mocker.MagicMock()

        mockApply = mocker.patch.object(ElasticClient, 'applyFilters')
        mockApply.return_value = mockSearch
        mockApplyAggs = mocker.patch.object(ElasticClient, 'applyAggregations')

        ElasticClient.addFilterClausesAndAggregations(mockSearch, [('format', 'test1'), ('format', 'test2')], 1)

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
            mocker.call('terms', editions__formats=['test1', 'test2'])
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
            mocker.call('filter', terms={'editions.formats': ['test1', 'test2']})
        ])

        mockApply.assert_called_once_with(mockSearch, [], ['formatFilter', 'displayFilter'], size=1)
        mockApplyAggs.assert_called_once_with(mockSearch, ['formatAggregation', 'displayAggregation'])

    def test_addFilterClausesAndAggregations_w_language(self, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['displayFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['displayAggregation']

        mockSearch = mocker.MagicMock()

        mockApply = mocker.patch.object(ElasticClient, 'applyFilters')
        mockApply.return_value = mockSearch
        mockApplyAggs = mocker.patch.object(ElasticClient, 'applyAggregations')

        ElasticClient.addFilterClausesAndAggregations(mockSearch, [('language', 'Test1')], 1)

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
        ])

        mockApply.assert_called_once_with(mockSearch, [('language', 'Test1')], ['displayFilter'], size=1)
        mockApplyAggs.assert_called_once_with(mockSearch, ['displayAggregation'])

    def test_addFilterClausesAndAggregations_no_filters(self, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockAgg = mocker.patch('api.elastic.A')

        mockSearch = mocker.MagicMock()

        mockApply = mocker.patch.object(ElasticClient, 'applyFilters')
        mockApply.return_value = mockSearch
        mockApplyAggs = mocker.patch.object(ElasticClient, 'applyAggregations')

        ElasticClient.addFilterClausesAndAggregations(mockSearch, [('showAll', 'true')], 1)

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
        ])

        mockApply.assert_called_once_with(mockSearch, [], [], size=1)
        mockApplyAggs.assert_called_once_with(mockSearch, [])

    def test_geneateDateRange_start_end(self):
        testRange = ElasticClient.generateDateRange([('startYear', 1900), ('endYear', 2000)])

        assert testRange['gte'] == 1900
        assert testRange['lte'] == 2000

    def test_geneateDateRange_start_only(self):
        testRange = ElasticClient.generateDateRange([('startYear', 1900)])

        assert testRange['gte'] == 1900
        assert 'lte' not in testRange.keys()

    def test_geneateDateRange_end_only(self):
        testRange = ElasticClient.generateDateRange([('endYear', 2000)])

        assert testRange['lte'] == 2000
        assert 'gte' not in testRange.keys()

    def test_applyFilters_no_language_filters(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.return_value = 'filterQuery'

        testQuery = ElasticClient.applyFilters(mockQuery, [], ['filter1', 'filter2'])

        assert testQuery == mockQuery
        mockClause.assert_called_once_with('bool', must=['filter1', 'filter2'])
        mockQuery.query.assert_called_once_with(
            'nested', path='editions', inner_hits={'size': 100}, query='filterQuery'
        )

    def test_applyFilters_language_filter_only(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.side_effect = [
            'Lang1Q', 'Lang1Bool', 'Lang1Filter', 'Lang1Nested',
            'Lang2Q', 'Lang2Bool', 'Lang2Filter', 'Lang2Nested'
        ]

        testQuery = ElasticClient.applyFilters(mockQuery, [('language', 'Test1'), ('langauge', 'Test2')], [])

        assert testQuery == mockQuery
        mockClause.assert_has_calls([
            mocker.call('term', editions__languages__language='Test1'),
            mocker.call('nested', path='editions.languages', query='Lang1Q'),
            mocker.call('bool', must=['Lang1Bool']),
            mocker.call('nested', path='editions', inner_hits={'size': 100}, query='Lang1Filter'),
            mocker.call('term', editions__languages__language='Test2'),
            mocker.call('nested', path='editions.languages', query='Lang2Q'),
            mocker.call('bool', must=['Lang2Bool']),
            mocker.call('nested', path='editions', query='Lang2Filter')
        ])
        mockQuery.query.assert_called_once_with('bool', must=['Lang1Nested', 'Lang2Nested'])

    def test_applyFilters_language_and_other_filters(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.side_effect = [
            'Lang1Q', 'Lang1Bool', 'Lang1Filter', 'Lang1Nested',
        ]

        testQuery = ElasticClient.applyFilters(mockQuery, [('language', 'Test1'), ], ['formatFilter'])

        assert testQuery == mockQuery
        mockClause.assert_has_calls([
            mocker.call('term', editions__languages__language='Test1'),
            mocker.call('nested', path='editions.languages', query='Lang1Q'),
            mocker.call('bool', must=['formatFilter', 'Lang1Bool']),
            mocker.call('nested', path='editions', inner_hits={'size': 100}, query='Lang1Filter'),
        ])
        mockQuery.query.assert_called_once_with('bool', must=['Lang1Nested'])

    def test_applyFilters_no_filters(self, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.return_value = 'filterQuery'

        testQuery = ElasticClient.applyFilters(mockQuery, [], [])

        assert testQuery == mockQuery
        mockClause.assert_called_once_with('match_all')
        mockQuery.query.assert_called_once_with(
            'nested', path='editions', inner_hits={'size': 100}, query='filterQuery'
        )

    def test_applyAggregations(self, mocker):
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.return_value = 'baseAgg'
        mockRoot = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        mockQuery.aggs.bucket.return_value = mockRoot
        mockRoot.bucket.return_value = mockRoot

        ElasticClient.applyAggregations(mockQuery, ['testAgg'])

        mockAgg.assert_called_once_with('nested', path='editions')
        mockQuery.aggs.bucket.assert_called_once_with('editions', 'baseAgg')
        mockRoot.bucket.assert_has_calls([
            mocker.call('edition_filter_0', 'testAgg'),
            mocker.call('lang_parent', 'nested', path='editions.languages'),
            mocker.call('languages', 'terms', field='editions.languages.language', size=200),
            mocker.call('editions_per', 'reverse_nested'),
            mocker.call('formats', 'terms', field='editions.formats', size=10),
            mocker.call('editions_per', 'reverse_nested')
        ])
