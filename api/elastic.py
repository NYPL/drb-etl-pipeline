from copy import deepcopy
import os
import re

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

    FORMAT_CROSSWALK = {
        'epub_zip': 'application/epub+zip',
        'epub_xml': 'application/epub+xml',
        'html': 'text/html',
        'html_edd': 'application/html+edd',
        'pdf': 'application/pdf',
        'webpub_json': 'application/webpub+json'
    }

    def __init__(self, esClient):
        self.client = esClient
        
        self.query = None

        self.dateSort = None

        self.languageFilters = []
        self.appliedFilters = []

        self.appliedAggregations = []
    
    def createSearch(self):
        return Search(using=self.client, index=os.environ['ELASTICSEARCH_INDEX'])

    def searchQuery(self, params, page=0, perPage=10):
        startPos, endPos = ElasticClient.getFromSize(page, perPage)
        search = self.createSearch()
        search.source(['uuid', 'editions'])

        searchClauses = []
        for field, query in params['query']:
            escapedQuery = self.escapeSearchQuery(query)

            if field is None or field in ['keyword', 'query']:
                searchClauses.append(Q('bool',
                    should=[
                        ElasticClient.titleQuery(escapedQuery),
                        ElasticClient.authorQuery(escapedQuery),
                        ElasticClient.subjectQuery(escapedQuery)
                    ]
                ))
            elif field == 'title':
                searchClauses.append(ElasticClient.titleQuery(escapedQuery))
            elif field == 'author':
                searchClauses.append(ElasticClient.authorQuery(escapedQuery))
            elif field == 'subject':
                searchClauses.append(ElasticClient.subjectQuery(escapedQuery))
            elif field == 'viaf' or field == 'lcnaf':
                searchClauses.append(ElasticClient.authorityQuery(field, escapedQuery))
            else:
                searchClauses.append(Q('match', **{field: escapedQuery}))

        self.query = search.query(Q('bool', must=searchClauses))

        self.createFilterClausesAndAggregations(params['filter'])

        self.addSortClause(params['sort'])
        self.addFiltersAndAggregations(3)

        return self.query[startPos:endPos].execute()

    @staticmethod
    def escapeSearchQuery(query):
        return re.sub(r'[\+\-\&\|\!\(\)\[\]\{\}\^\~\?\:\\]{1}', '\\\\\g<0>', query)

    def languageQuery(self, workTotals):
        search = self.createSearch()

        query = search.query(Q())[:0]

        languageAgg = query.aggs.bucket('languages', A('nested', path='editions.languages'))\
            .bucket('languages', 'terms', **{'field': 'editions.languages.language', 'size': 250})

        if workTotals:
            languageAgg.bucket('work_totals', 'reverse_nested')

        return query.execute()

    @classmethod
    def titleQuery(cls, titleText):
        return Q('bool',
            should=[
                Q('query_string', query=titleText, fields=['title', 'alt_titles'], default_operator='and'),
                Q('nested', path='editions', query=Q('query_string', query=titleText, fields=['editions.title'], default_operator='and'))
            ]
        )

    @classmethod
    def authorQuery(cls, authorText):
        workAgentQuery = Q('bool',
            must=[Q('query_string', query=authorText, fields=['agents.name'], default_operator='and')],
            must_not=[Q('terms', agents__roles=cls.ROLE_BLOCKLIST)]
        )
        editionAgentQuery = Q('bool',
            must=[Q('query_string', query=authorText, fields=['editions.agents.name'], default_operator='and')],
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
        return Q('nested', path='subjects', query=Q('query_string', query=subjectText, fields=['subjects.heading'], default_operator='and'))
    
    @staticmethod
    def getFromSize(page, perPage):
        startPos = page * perPage
        endPos = startPos + perPage
        return startPos, endPos

    def addSortClause(self, sortParams):
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
                sortFilters = [f.to_dict() for f in self.appliedFilters]

                if len(self.languageFilters) > 0:
                    sortFilters.extend([l.to_dict() for l in self.languageFilters])

                self.dateSort = {
                    'editions.publication_date': {
                        'order': sortDir,
                        'nested': {
                            'path': 'editions',
                            'filter': {'bool': {'must': sortFilters}}
                        }
                    }
                }

                sortValues.append(self.dateSort)

        sortValues.append({'uuid': 'asc'})
        
        self.query = self.query.sort(*sortValues)
    
    def createFilterClausesAndAggregations(self, filterParams):
        dateFilters = list(filter(lambda x: 'year' in x[0].lower(), filterParams))
        languageFilters = list(filter(lambda x: x[0] == 'language', filterParams))
        formatFilters = list(filter(lambda x: x[0] == 'format', filterParams))
        displayFilters = list(filter(lambda x: x[0] == 'showAll', filterParams))

        dateFilter, dateAggregation = (None, None)
        formatFilter, formatAggregation = (None, None)
        displayFilter, displayAggregation = (Q('exists', field='editions.formats'), A('filter', **{'exists': {'field': 'editions.formats'}}))

        if len(languageFilters) > 0:
            self.languageFilters = [
                Q('nested', path='editions.languages', query=Q('term', editions__languages__language=language[1]))
                for language in languageFilters
            ]

        if len(dateFilters) > 0:
            dateRange = ElasticClient.generateDateRange(dateFilters)
            dateFilter = Q('range', **{'editions.publication_date': dateRange})
            dateAggregation = A('filter', **{'range': {'editions.publication_date': dateRange}})

        if len(formatFilters) > 0:
            formats = []
            for format in formatFilters:
                try:
                    formats.append(self.FORMAT_CROSSWALK[format[1]])
                except KeyError:
                    raise ElasticClientError('Invalid format filter {} received'.format(format[1]))

            formatFilter = Q('terms', editions__formats=formats)
            formatAggregation = A('filter', **{'terms': {'editions.formats': formats}})

        if len(displayFilters) > 0 and displayFilters[0][1] == 'true':
            displayFilter = None
            displayAggregation = None
        
        self.appliedFilters = list(filter(None, [dateFilter, formatFilter, displayFilter]))
        self.appliedAggregations = list(filter(None, [dateAggregation, formatAggregation, displayAggregation]))

    def addFiltersAndAggregations(self, innerHits):
        self.applyFilters(size=innerHits)
        self.applyAggregations()

    @staticmethod
    def generateDateRange(dateFilters):
        filterRange = {}
        for field, value in dateFilters:
            if field == 'startYear':
                filterRange['gte'] = value
            elif field == 'endYear':
                filterRange['lte'] = value

        return filterRange

    def applyFilters(self, size=100):
        innerHitsClause = {'size': size}

        if self.dateSort:
            innerHitSort = deepcopy(self.dateSort)
            del innerHitSort['editions.publication_date']['nested']

            innerHitsClause['sort'] = innerHitSort

        if len(self.languageFilters) > 0:
            filters = []
            for i, langFilter in enumerate(self.languageFilters):
                filterSet = self.appliedFilters + [langFilter]
                if i == 0:
                    filters.append(Q('nested', path='editions', inner_hits=innerHitsClause, query=Q('bool', must=filterSet)))
                else:
                    filters.append(Q('nested', path='editions', query=Q('bool', must=filterSet)))
            
            self.query = self.query.query('bool', must=filters)
        elif len(self.appliedFilters) > 0:
            self.query = self.query.query('nested', path='editions', inner_hits=innerHitsClause, query=Q('bool', must=self.appliedFilters))
        else:
            self.query = self.query.query('nested', path='editions', inner_hits=innerHitsClause, query=Q('match_all'))

    def applyAggregations(self):
        rootAgg = self.query.aggs.bucket('editions', A('nested', path='editions'))

        lastAgg = rootAgg
        for i, agg in enumerate(self.appliedAggregations):
            currentAgg = 'edition_filter_{}'.format(i)
            lastAgg = lastAgg.bucket(currentAgg, agg)
        
        lastAgg.bucket('lang_parent', 'nested', path='editions.languages')\
            .bucket('languages', 'terms', **{'field': 'editions.languages.language', 'size': 200})\
            .bucket('editions_per', 'reverse_nested')

        lastAgg.bucket('formats', 'terms', **{'field': 'editions.formats', 'size': 10})\
            .bucket('editions_per', 'reverse_nested')


class ElasticClientError(Exception):
    pass
