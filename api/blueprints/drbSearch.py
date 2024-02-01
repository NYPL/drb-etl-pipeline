from flask import Blueprint, request, current_app
from ..elastic import ElasticClient, ElasticClientError
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

search = Blueprint('search', __name__, url_prefix='/search')


@search.route('', methods=['GET'])
def standardQuery():
    esClient = ElasticClient(current_app.config['REDIS_CLIENT'])
    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    searchParams = APIUtils.normalizeQueryParams(request.args)

    terms = {}
    for param in ['query', 'sort', 'filter', 'showAll']:
        terms[param] = APIUtils.extractParamPairs(param, searchParams)

    if terms.get('showAll', None):
        terms['filter'].append(terms['showAll'][0])
        del terms['showAll']

    searchPage = int(searchParams.get('page', [1])[0]) - 1
    searchSize = int(searchParams.get('size', [10])[0])

    readerVersion = searchParams.get('readerVersion', [None])[0]\
        or current_app.config['READER_VERSION']

    logger.info('Executing ES Query {} with filters {}'.format(
        searchParams, terms['filter'])
    )

    try:
        searchResult = esClient.searchQuery(
            terms, page=searchPage, perPage=searchSize
        )
    except ElasticClientError as e:
        return APIUtils.formatResponseObject(
            400, 'searchResponse', {'message': str(e)}
        )

    results = []
    for res in searchResult.hits:
        editionIds = [e.edition_id for e in res.meta.inner_hits.editions.hits]

        try:
            highlights = {
                key: list(set(res.meta.highlight[key]))
                for key in res.meta.highlight
            }
        except AttributeError:
            highlights = {}

        results.append((res.uuid, editionIds, highlights))

    if esClient.sortReversed is True:
        results = [r for r in reversed(results)]

    filteredFormats = APIUtils.formatFilters(terms)

    logger.info('Executing DB Query for {} editions'.format(len(results)))

    works = dbClient.fetchSearchedWorks(results)
    facets = APIUtils.formatAggregationResult(
        searchResult.aggregations.to_dict()
    )

    paging = APIUtils.formatPagingOptions(
        searchPage + 1, searchSize, searchResult.hits.total.value
    )

    dataBlock = {
        'totalWorks': searchResult.hits.total.value,
        'works': APIUtils.formatWorkOutput(
            works, results, request=request, dbClient=dbClient, formats=filteredFormats, reader=readerVersion
        ),
        'paging': paging,
        'facets': facets
    }

    logger.debug('Search Query 200 on /search')

    dbClient.closeSession()

    return APIUtils.formatResponseObject(200, 'searchResponse', dataBlock)
