import pytest

from tests.helper import TestHelpers
from api.elastic import ElasticClient, ElasticClientError


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
        mockSearch.query.return_value = mockSearch
        mockSearch.__getitem__.return_value = mockSearch
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
            createFilterClausesAndAggregations=mocker.DEFAULT,
            addSortClause=mocker.DEFAULT,
            addFiltersAndAggregations=mocker.DEFAULT,
            escapeSearchQuery=mocker.DEFAULT
        )

    def test_createSearch(self, testInstance, mocker):
        mockSearch = mocker.patch('api.elastic.Search')
        mockSearch.return_value = 'searchClient'

        searchClient = testInstance.createSearch()

        assert searchClient == 'searchClient'
        mockSearch.assert_called_once_with(using=testInstance.client, index='test_es_index')

    def test_searchQuery_keyword_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['authorQuery'].return_value = 'authorQuery'
        searchMocks['subjectQuery'].return_value = 'subjectQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
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
        searchMocks['escapeSearchQuery'].assert_has_calls([mocker.call('test'), mocker.call('test2')])
        searchMocks['titleQuery'].assert_has_calls([mocker.call('escapedQuery'), mocker.call('escapedQuery')])
        searchMocks['authorQuery'].assert_has_calls([mocker.call('escapedQuery'), mocker.call('escapedQuery')])
        searchMocks['subjectQuery'].assert_has_calls([mocker.call('escapedQuery'), mocker.call('escapedQuery')])
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_title_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('title', 'test'), ], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['titleQuery'])
        searchMocks['escapeSearchQuery'].assert_called_once_with('test')
        searchMocks['titleQuery'].assert_called_once_with('escapedQuery')
        searchMocks['authorQuery'].assert_not_called()
        searchMocks['subjectQuery'].assert_not_called()
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_author_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorQuery'].return_value = 'authorQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('author', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['authorQuery'])
        searchMocks['escapeSearchQuery'].assert_called_once_with('test')
        searchMocks['titleQuery'].assert_not_called()
        searchMocks['authorQuery'].assert_called_once_with('escapedQuery')
        searchMocks['subjectQuery'].assert_not_called()
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_subject_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['subjectQuery'].return_value = 'subjectQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('subject', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['subjectQuery'])
        searchMocks['escapeSearchQuery'].assert_called_once_with('test')
        searchMocks['titleQuery'].assert_not_called()
        searchMocks['authorQuery'].assert_not_called()
        searchMocks['subjectQuery'].assert_called_once_with('escapedQuery')
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_authority_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorityQuery'].return_value = 'authorityQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('viaf', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        mockQuery.assert_called_once_with('bool', must=['authorityQuery'])
        searchMocks['escapeSearchQuery'].assert_called_once_with('test')
        searchMocks['titleQuery'].assert_not_called()
        searchMocks['authorQuery'].assert_not_called()
        searchMocks['subjectQuery'].assert_not_called()
        searchMocks['authorityQuery'].assert_called_once_with('viaf', 'escapedQuery')

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_generic_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
        searchMocks['addSortClause'].return_value = mockSearch

        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['genericQuery', 'searchClauses']

        queryResult = testInstance.searchQuery({
            'query': [('other', 'test'),], 'sort': ['sort'], 'filter': ['filter']
        })

        assert queryResult == 'searchResult'
        searchMocks['getFromSize'].assert_called_once_with(0, 10)
        searchMocks['escapeSearchQuery'].assert_called_once_with('test')
        mockQuery.assert_has_calls([
            mocker.call('match', other='escapedQuery'),
            mocker.call('bool', must=['genericQuery'])
        ])
        searchMocks['titleQuery'].assert_not_called()
        searchMocks['authorQuery'].assert_not_called()
        searchMocks['subjectQuery'].assert_not_called()
        searchMocks['authorityQuery'].assert_not_called()

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)

        mockSearch.execute.assert_called_once()

    def test_searchQuery_multi_search(self, testInstance, mockSearch, searchMocks, mocker):
        searchMocks['createSearch'].return_value = mockSearch
        searchMocks['escapeSearchQuery'].return_value = 'escapedQuery'
        searchMocks['getFromSize'].return_value = (0, 10)
        searchMocks['authorityQuery'].return_value = 'authorityQuery'
        searchMocks['titleQuery'].return_value = 'titleQuery'
        searchMocks['createFilterClausesAndAggregations'].return_value = mockSearch
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
        searchMocks['escapeSearchQuery'].assert_has_calls([mocker.call('testTitle'), mocker.call('test')])
        mockQuery.assert_called_once_with('bool', must=['titleQuery', 'authorityQuery'])
        searchMocks['titleQuery'].assert_called_once_with('escapedQuery')
        searchMocks['authorQuery'].assert_not_called()
        searchMocks['subjectQuery'].assert_not_called()
        searchMocks['authorityQuery'].assert_called_once_with('lcnaf', 'escapedQuery')

        mockSearch.query.assert_called_once_with('searchClauses')

        searchMocks['createFilterClausesAndAggregations'].assert_called_once_with(['filter'])
        searchMocks['addSortClause'].assert_called_once_with(['sort'])
        searchMocks['addFiltersAndAggregations'].assert_called_once_with(3)
        
        mockSearch.execute.assert_called_once()

    def test_escapeSearchQuery_changed(self):
        assert ElasticClient.escapeSearchQuery('[test]+a:thing!') == '\[test\]\+a\:thing\!'

    def test_escapeSearchQuery_unchanged(self):
        assert ElasticClient.escapeSearchQuery('a simple query') == 'a simple query'

    def test_titleQuery(self):
        testQueryES = ElasticClient.titleQuery('testTitle')
        testQuery = testQueryES.to_dict()

        assert testQuery['bool']['should'][0]['query_string']['query'] == 'testTitle'
        assert testQuery['bool']['should'][0]['query_string']['fields'] == ['title', 'alt_titles']
        assert testQuery['bool']['should'][1]['nested']['path'] == 'editions'
        assert testQuery['bool']['should'][1]['nested']['query']['query_string']['query'] == 'testTitle'
        assert testQuery['bool']['should'][1]['nested']['query']['query_string']['fields'] == ['editions.title']
        assert testQuery['bool']['should'][1]['nested']['query']['query_string']['default_operator'] == 'and'

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
    
    def test_addSortClause_title_w_direction(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        testInstance.query = mockQuery
        testInstance.addSortClause([('title', 'DESC')])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'sort_title': {'order': 'DESC'}}, {'uuid': 'asc'}
        )
    
    def test_addSortClause_title_wo_direction(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        testInstance.query = mockQuery
        testInstance.addSortClause([('title', None)])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'sort_title': {'order': 'ASC'}}, {'uuid': 'asc'}

        )
    
    def test_addSortClause_author(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        testInstance.query = mockQuery
        testInstance.addSortClause([('author', 'ASC')])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {'agents.sort_name': {'order': 'ASC', 'nested': {'path': 'agents', 'filter': {'terms': {'agents.roles': ['author']}}, 'max_children': 1}}},
            {'uuid': 'asc'}
        )
    
    def test_addSortClause_date_w_filters(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        mockFilter = mocker.MagicMock()
        mockFilter.to_dict.return_value = 'testFilter'

        testInstance.appliedFilters = [mockFilter]
        testInstance.languageFilters = []

        testInstance.query = mockQuery
        testInstance.addSortClause([('date', 'DESC')])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {
                'editions.publication_date': {
                    'order': 'DESC',
                    'nested': {
                        'path': 'editions',
                        'filter': {'bool': {'must': ['testFilter']}}
                    }
                }
            },
            {'uuid': 'asc'}
        )
    
    def test_addSortClause_date_w_filters_and_language(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        mockFilter = mocker.MagicMock()
        mockFilter.to_dict.side_effect = ['testFilter', 'testLangFilter']

        testInstance.appliedFilters = [mockFilter]
        testInstance.languageFilters = [mockFilter]

        testInstance.query = mockQuery
        testInstance.addSortClause([('date', 'DESC')])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with(
            {
                'editions.publication_date': {
                    'order': 'DESC',
                    'nested': {
                        'path': 'editions',
                        'filter': {'bool': {'must': ['testFilter', 'testLangFilter']}}
                    }
                }
            },
            {'uuid': 'asc'}
        )
    
    def test_addSortClause_root_sort_only(self, testInstance, mocker):
        mockQuery = mocker.MagicMock()
        mockQuery.sort.return_value = 'sortQuery'

        testInstance.query = mockQuery
        testInstance.addSortClause([])

        assert testInstance.query == 'sortQuery'
        mockQuery.sort.assert_called_once_with({'uuid': 'asc'})

    def test_createFilterClausesAndAggregations_default(self, testInstance, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.return_value = 'formatFilter'
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.return_value = 'formatAggregation'

        testInstance.createFilterClausesAndAggregations([])

        mockQuery.assert_called_once_with('exists', field='editions.formats')
        mockAgg.assert_called_once_with('filter', exists={'field': 'editions.formats'})

        assert testInstance.appliedFilters == ['formatFilter']
        assert testInstance.appliedAggregations == ['formatAggregation']

    def test_createFilterClausesAndAggregations_w_date(self, testInstance, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['dateFilter', 'formatFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['dateAggregation', 'formatAggregation']

        mockGenerateRange = mocker.patch.object(ElasticClient, 'generateDateRange')
        mockGenerateRange.return_value = 'testRange'

        testInstance.createFilterClausesAndAggregations([('startYear', 1900)])

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
            mocker.call('range', **{'editions.publication_date': 'testRange'})
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
            mocker.call('filter', range={'editions.publication_date': 'testRange'})
        ])

        assert testInstance.appliedFilters == ['formatFilter', 'dateFilter']
        assert testInstance.appliedAggregations == ['formatAggregation', 'dateAggregation']

    def test_createFilterClausesAndAggregations_w_format(self, testInstance, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['displayFilter', 'formatFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['displayAggregation', 'formatAggregation']

        testInstance.createFilterClausesAndAggregations([('format', 'pdf'), ('format', 'html_edd')])

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
            mocker.call('terms', editions__formats=['application/pdf', 'application/html+edd'])
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
            mocker.call('filter', terms={'editions.formats': ['application/pdf', 'application/html+edd']})
        ])

        assert testInstance.appliedFilters == ['formatFilter', 'displayFilter']
        assert testInstance.appliedAggregations == ['formatAggregation', 'displayAggregation']

    def test_createFilterClausesAndAggregations_w_format_error(self, testInstance):
        with pytest.raises(ElasticClientError):
            testInstance.createFilterClausesAndAggregations([('format', 'test')])

    def test_createFilterClausesAndAggregations_w_language(self, testInstance, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockQuery.side_effect = ['displayFilter', 'innerLang', 'languageFilter']
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.side_effect = ['displayAggregation']

        testInstance.createFilterClausesAndAggregations([('language', 'Test1')])

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
            mocker.call('term', editions__languages__language='Test1'),
            mocker.call('nested', path='editions.languages', query='innerLang')
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
        ])

        assert testInstance.languageFilters == ['languageFilter']
        assert testInstance.appliedFilters == ['displayFilter']
        assert testInstance.appliedAggregations == ['displayAggregation']

    def test_createFilterClausesAndAggregations_no_filters(self, testInstance, mocker):
        mockQuery = mocker.patch('api.elastic.Q')
        mockAgg = mocker.patch('api.elastic.A')

        testInstance.createFilterClausesAndAggregations([('showAll', 'true')])

        mockQuery.assert_has_calls([
            mocker.call('exists', field='editions.formats'),
        ])
        mockAgg.assert_has_calls([
            mocker.call('filter', exists={'field': 'editions.formats'}),
        ])

        assert testInstance.appliedFilters == []
        assert testInstance.appliedAggregations == []

    def test_addFiltersAndAggregations(self, testInstance, mocker):
        mockFilters = mocker.patch.object(ElasticClient, 'applyFilters')
        mockAggregations = mocker.patch.object(ElasticClient, 'applyAggregations')

        testInstance.addFiltersAndAggregations(1)

        mockFilters.assert_called_once_with(size=1)
        mockAggregations.assert_called_once()

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

    def test_applyFilters_no_language_filters(self, testInstance, mocker):
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.return_value = 'filterQuery'

        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        testInstance.query = mockQuery
        testInstance.dateSort = None
        testInstance.appliedFilters = ['filter1', 'filter2']
        testInstance.languageFilters = []

        testInstance.applyFilters()

        mockClause.assert_called_once_with('bool', must=['filter1', 'filter2'])
        testInstance.query.query.assert_called_once_with(
            'nested', path='editions', inner_hits={'size': 100}, query='filterQuery'
        )

    def test_applyFilters_language_filter_only(self, testInstance, mocker):
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.side_effect = [
            'Lang1Filter', 'Lang1Nested', 'Lang2Filter', 'Lang2Nested'
        ]

        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        testInstance.query = mockQuery
        testInstance.dateSort = None
        testInstance.appliedFilters = []
        testInstance.languageFilters = ['Lang1', 'Lang2']

        testInstance.applyFilters()

        mockClause.assert_has_calls([
            mocker.call('bool', must=['Lang1']),
            mocker.call('nested', path='editions', inner_hits={'size': 100}, query='Lang1Filter'),
            mocker.call('bool', must=['Lang2']),
            mocker.call('nested', path='editions', query='Lang2Filter')
        ])
        mockQuery.query.assert_called_once_with('bool', must=['Lang1Nested', 'Lang2Nested'])

    def test_applyFilters_language_and_other_filters(self, testInstance, mocker):
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.side_effect = ['Lang1Filter', 'Lang1Nested']

        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        testInstance.query = mockQuery
        testInstance.dateSort = None
        testInstance.appliedFilters = ['formatFilter']
        testInstance.languageFilters = ['Lang1']

        testInstance.applyFilters()

        mockClause.assert_has_calls([
            mocker.call('bool', must=['formatFilter', 'Lang1']),
            mocker.call('nested', path='editions', inner_hits={'size': 100}, query='Lang1Filter'),
        ])
        mockQuery.query.assert_called_once_with('bool', must=['Lang1Nested'])

    def test_applyFilters_no_filters_date_ort(self, testInstance, mocker):
        mockClause = mocker.patch('api.elastic.Q')
        mockClause.return_value = 'filterQuery'

        mockQuery = mocker.MagicMock()
        mockQuery.query.return_value = mockQuery
        testInstance.query = mockQuery
        testInstance.dateSort = {'editions.publication_date': {'test': 'value', 'nested': 'toDelete'}}
        testInstance.appliedFilters = []
        testInstance.languageFilters = []

        testInstance.applyFilters()

        mockClause.assert_called_once_with('match_all')
        mockQuery.query.assert_called_once_with(
            'nested',
            path='editions',
            inner_hits={'size': 100, 'sort': {'editions.publication_date': {'test': 'value'}}},
            query='filterQuery'
        )

    def test_applyAggregations(self, testInstance, mocker):
        mockAgg = mocker.patch('api.elastic.A')
        mockAgg.return_value = 'baseAgg'
        mockRoot = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        mockQuery.aggs.bucket.return_value = mockRoot
        mockRoot.bucket.return_value = mockRoot

        testInstance.query = mockQuery
        testInstance.appliedAggregations = ['testAgg']
        testInstance.applyAggregations()

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
