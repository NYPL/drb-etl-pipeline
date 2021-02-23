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
    queryTerms = APIUtils.extractParamPairs(searchParams.get('query', []))
    sortTerms = APIUtils.extractParamPairs(searchParams.get('sort', []))

    filterTerms = APIUtils.extractParamPairs(searchParams.get('filter', []))
    filterTerms.extend(APIUtils.extractParamPairs(searchParams.get('showAll', [])))

    searchPage = searchParams.get('page', [0])[0]
    searchSize = searchParams.get('size', [10])[0]

    logger.info('Executing ES Query {} with filters {}'.format(searchParams, filterTerms))

    searchResult = esClient.searchQuery(queryTerms, sortTerms, filterTerms, page=searchPage, perPage=searchSize)

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
