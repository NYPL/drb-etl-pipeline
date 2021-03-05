from flask import Blueprint, jsonify, current_app, request

from ..db import DBClient
from ..elastic import ElasticClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)


utils = Blueprint('utils', __name__, url_prefix='/utils')

@utils.route('/languages', methods=['GET'])
def languageCounts():
    esClient = ElasticClient(current_app.config['ES_CLIENT'])

    reqParams = APIUtils.normalizeQueryParams(request.args)
    workCounts = reqParams.get('totals', ['true'])[0].lower() != 'false'

    langResult = esClient.languageQuery(workCounts)

    languageList = APIUtils.formatLanguages(langResult.aggregations, workCounts)

    logger.debug('Language list 200 OK on /utils/languages')

    return APIUtils.formatResponseObject(200, 'languageCounts', languageList)

@utils.route('/counts', methods=['GET'])
def totalCounts():
    dbClient = DBClient(current_app.config['DB_CLIENT'])

    totalResult = dbClient.fetchRowCounts()

    totalsSummary = APIUtils.formatTotals(totalResult)

    return APIUtils.formatResponseObject(200, 'totalCounts', totalsSummary)
