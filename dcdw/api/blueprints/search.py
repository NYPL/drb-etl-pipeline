from flask import (
    Blueprint, request, session, url_for, redirect, current_app, jsonify
)
from ..elastic import ElasticClient
from ..db import DBClient
from ..utils import APIUtils

search = Blueprint('search', __name__, url_prefix='/search')

@search.route('/', methods=['GET'])
def standardQuery():
    esClient = ElasticClient(current_app.config['ES_CLIENT'])
    dbClient = DBClient(current_app.config['DB_CLIENT'])

    searchParams = APIUtils.normalizeQueryParams(request.args)
    queryTerms = APIUtils.extractParamPairs(searchParams.get('query', []))
    sortTerms = APIUtils.extractParamPairs(searchParams.get('sort', []))
    filterTerms = APIUtils.extractParamPairs(searchParams.get('filter', []))

    searchPage = searchParams.get('page', [0])[0]
    searchSize = searchParams.get('size', [10])[0]

    searchResult = esClient.searchQuery(queryTerms, sortTerms, filterTerms, page=searchPage, perPage=searchSize)

    resultIds = [
        (r.uuid, [e.edition_id for e in r.meta.inner_hits.editions.hits])
        for r in searchResult.hits
    ]

    works = dbClient.fetchSearchedWorks(resultIds)
    facets = APIUtils.formatAggregationResult(searchResult.aggregations.to_dict())
    paging = APIUtils.formatPagingOptions(searchResult.hits)

    dataBlock = {
        'totalWorks': searchResult.hits.total,
        'works': APIUtils.formatWorkOutput(works, resultIds),
        'paging': paging,
        'facets': facets
    }

    return APIUtils.formatResponseObject(200, 'searchResponse', dataBlock)
