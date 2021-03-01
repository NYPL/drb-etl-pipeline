from flask import Blueprint, request, current_app
from ..elastic import ElasticClient
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

search = Blueprint('search', __name__, url_prefix='/search')

@search.route('/', methods=['GET'])
def standardQuery():
    esClient = ElasticClient(current_app.config['ES_CLIENT'])
    dbClient = DBClient(current_app.config['DB_CLIENT'])

    searchParams = APIUtils.normalizeQueryParams(request.args)

    terms = {}
    for param in ['query', 'sort', 'filter', 'showAll']:
        terms[param] = APIUtils.extractParamPairs(param, searchParams)

    if terms.get('showAll', None):
        terms['filter'].append(terms['showAll'][0])

    searchPage = searchParams.get('page', [0])[0]
    searchSize = searchParams.get('size', [10])[0]

    logger.info('Executing ES Query {} with filters {}'.format(searchParams, terms['filter']))

    searchResult = esClient.searchQuery(terms, page=searchPage, perPage=searchSize)

    resultIds = [
        (r.uuid, [e.edition_id for e in r.meta.inner_hits.editions.hits])
        for r in searchResult.hits
    ]

    logger.info('Executing DB Query for {} editions'.format(len(resultIds)))

    works = dbClient.fetchSearchedWorks(resultIds)
    facets = APIUtils.formatAggregationResult(searchResult.aggregations.to_dict())
    paging = APIUtils.formatPagingOptions(searchResult.hits)

    dataBlock = {
        'totalWorks': searchResult.hits.total,
        'works': APIUtils.formatWorkOutput(works, resultIds),
        'paging': paging,
        'facets': facets
    }

    logger.debug('Search Query 200 on /search')

    return APIUtils.formatResponseObject(200, 'searchResponse', dataBlock)
