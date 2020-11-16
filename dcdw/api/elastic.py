import os

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A

class ElasticClient():
    ROLE_BLOCKLIST = ['arl', 'binder', 'binding designer', 'book designer',
        'book producer', 'bookseller', 'collector', 'consultant', 'contractor',
        'corrector', 'dedicatee', 'donor', 'copyright holder', 'court reporter',
        'electrotyper', 'engineer', 'engraver', 'expert', 'former owner', 'funder',
        'honoree', 'host institution', 'imprint', 'inscriber', 'other', 'patron',
        'performer', 'presenter', 'producer', 'production company', 'publisher',
        'printer', 'printer of plates', 'printmaker', 'proofreader',
        'publishing director', 'retager', 'secretary', 'sponsor', 'stereotyper',
        'thesis advisor', 'transcriber', 'typographer', 'woodcutter',
    ]

    def __init__(self, esClient):
        self.client = esClient
    
    def createSearch(self):
        return Search(using=self.client, index=os.environ['ES_INDEX'])

    def searchQuery(self, searchParams, sortParams, filterParams, page=0, perPage=10):
        startPos, endPos = ElasticClient.getFromSize(page, perPage)
        search = self.createSearch()
        search.source(['uuid', 'editions'])

        searchClauses = []
        for field, query in searchParams:
            if field is None or field == 'keyword':
                searchClauses.append(Q('bool',
                    should=[
                        ElasticClient.titleQuery(query),
                        ElasticClient.authorQuery(query),
                        ElasticClient.subjectQuery(query)
                    ]
                ))
            elif field == 'title':
                searchClauses.append(ElasticClient.titleQuery(query))
            elif field == 'author':
                searchClauses.append(ElasticClient.authorQuery(query))
            elif field == 'subject':
                searchClauses.append(ElasticClient.subjectQuery(query))
            elif field == 'viaf' or field == 'lcnaf':
                searchClauses.append(ElasticClient.authorityQuery(field, query))
            else:
                searchClauses.append(Q('match', **{field: query}))

        coreSearch = search.query(Q('bool', must=searchClauses))[startPos:endPos]

        coreSearch = ElasticClient.addFilterClausesAndAggregations(coreSearch, filterParams)

        coreSearch = ElasticClient.addSortClause(coreSearch, sortParams)

        return coreSearch.execute()

    @classmethod
    def titleQuery(cls, titleText):
        return Q('bool',
            should=[
                Q('query_string', query=titleText, fields=['title', 'alt_titles']),
                Q('nested', path='editions', query=Q('query_string', query=titleText, fields=['editions.title']))
            ]
        )

    @classmethod
    def authorQuery(cls, authorText):
        workAgentQuery = Q('bool',
            must=[Q('query_string', query=authorText, fields=['agents.name'])],
            must_not=[Q('terms', agents__roles=cls.ROLE_BLOCKLIST)]
        )
        editionAgentQuery = Q('bool',
            must=[Q('query_string', query=authorText, fields=['editions.agents.name'])],
            must_not=[Q('terms', editions__agents__roles=cls.ROLE_BLOCKLIST)]
        )

        return Q('bool',
            should=[
                Q('nested', path='agents', query=workAgentQuery),
                Q('nested', path='editions.agents', query=editionAgentQuery)
            ]
        )

    @classmethod
    def authorityQuery(cls, authority, authorityID):
        workAuthorityQuery = Q('term', **{'agents.{}'.format(authority): authorityID})
        editionAuthorityQuery = Q('term', **{'editions.agents.{}'.format(authority): authorityID})

        return Q('bool',
            should=[
                Q('nested', path='agents', query=workAuthorityQuery),
                Q('nested', path='editions.agents', query=editionAuthorityQuery)
            ]
        )

    @classmethod
    def subjectQuery(cls, subjectText):
        return Q('nested', path='subjects', query=Q('query_string', query=subjectText, fields=['subjects.heading']))
    
    @staticmethod
    def getFromSize(page, perPage):
        startPos = page * perPage
        endPos = startPos + perPage
        return startPos, endPos

    @staticmethod
    def addSortClause(query, sortParams):
        sortValues = []
        for sort, direction in sortParams:
            sortDir = direction or 'ASC'
            if sort == 'title':
                sortValues.append({'sort_title': {'order': sortDir}})
            elif sort == 'author':
                sortValues.append({
                    'agents.sort_name': {
                        'order': sortDir,
                        'nested': {
                            'path': 'agents',
                            'filter': {'terms': {'agents.roles': ['author']}},
                            'max_children': 1
                        }
                    }
                })
            elif sort == 'date':
                sortValues.append({
                    'publication_date': {
                        'order': sortDir,
                        'nested': {'path': 'editions'}
                    }
                })

        sortValues.append({'uuid': 'asc'})
        
        return query.sort(*sortValues)
    
    @staticmethod
    def addFilterClausesAndAggregations(query, filterParams):
        dateFilters = list(filter(lambda x: 'year' in x[0].lower(), filterParams))
        languageFilters = list(filter(lambda x: x[0] == 'language', filterParams))
        formatFilters = list(filter(lambda x: x[0] == 'format', filterParams))
        displayFilters = list(filter(lambda x: x[0] == 'show_all', filterParams))

        dateFilter, dateAggregation = (None, None)
        formatFilter, formatAggregation = (None, None)
        displayFilter, displayAggregation = (Q('exists', field='editions.formats'),A('filters', **{'exists': {'field': 'editions.formats'}}))

        if len(dateFilters) > 0:
            dateRange = ElasticClient.generateDateRange(dateFilters)
            dateFilter = Q('range', **{'editions.publication_date': dateRange})
            dateAggregation = A('filter', **{'range': {'editions.publication_date': dateRange}})

        if len(formatFilters) > 0:
            formats = [f[1] for f in formatFilters]
            formatFilter = Q('terms', instances__formats=formats)
            formatAggregation = A('filter', **{'terms': {'editions.formats': formats}})

        if len(displayFilters) == 0:
            displayFilter = None
            displayAggregation = None
        
        appliedFilters = list(filter(None, [dateFilter, formatFilter, displayFilter]))
        aggregationFilters = list(filter(None, [dateAggregation, formatAggregation, displayAggregation]))

        query = ElasticClient.applyFilters(query, languageFilters, appliedFilters)
        ElasticClient.applyAggregations(query, aggregationFilters)

        return query
    
    @staticmethod
    def generateDateRange(dateFilters):
        filterRange = {}
        for field, value in dateFilters:
            if field == 'startYear':
                filterRange['gte'] = value
            elif field == 'endYear':
                filterRange['lte'] = value

        return filterRange

    @staticmethod
    def applyFilters(query, languageFilters, appliedFilters):
        if len(languageFilters) > 0:
            filters = []
            for i, language in enumerate(languageFilters):
                langFilter = Q('nested', path='editions.languages', query=Q('term', editions__languages__language=language[1]))
                filterSet = appliedFilters + [langFilter]
                if i == 0:
                    filters.append(Q('nested', path='editions', inner_hits={'size': 100}, query=Q('bool', must=filterSet)))
                else:
                    filters.append(Q('nested', path='editions', query=Q('bool', must=filterSet)))
            
            query = query.query('bool', must=filters)
        elif len(appliedFilters) > 0:
            query = query.query('nested', path='editions', inner_hits={'size': 100}, query=Q('bool', must=appliedFilters))

        return query

    @staticmethod
    def applyAggregations(query, aggFilters):
        rootAgg = query.aggs.bucket('editions', A('nested', path='editions'))

        lastAgg = rootAgg
        for i, agg in enumerate(aggFilters):
            currentAgg = 'edition_filter_{}'.format(i)
            lastAgg = lastAgg.bucket(currentAgg, agg)
        
        lastAgg.bucket('lang_parent', 'nested', path='editions.languages')\
            .bucket('languages', 'terms', **{'field': 'editions.languages.language', 'size': 200})\
            .bucket('editions_per_language', 'reverse_nested')
