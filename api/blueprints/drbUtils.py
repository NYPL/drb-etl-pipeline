from flask import Blueprint, current_app, request, Response
from flask_cors import cross_origin
import os
import requests
from urllib.parse import unquote_plus, urlparse

from ..db import DBClient
from ..elastic import ElasticClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)


utils = Blueprint('utils', __name__, url_prefix='/utils')
EXCLUDED_HEADERS = [
    'content-encoding', 'content-length', 'transfer-encoding',
    'x-frame-options', 'referrer-policy', 'access-control-allow-origin',
    'connection', 'keep-alive', 'public', 'proxy-authenticate',
    'upgrade'
]


@utils.route('/languages', methods=['GET'])
def languageCounts():
    esClient = ElasticClient(current_app.config['REDIS_CLIENT'])

    reqParams = APIUtils.normalizeQueryParams(request.args)
    workCounts = reqParams.get('totals', ['true'])[0].lower() != 'false'

    langResult = esClient.languageQuery(workCounts)

    languageList = APIUtils.formatLanguages(
        langResult.aggregations, workCounts
    )

    logger.debug('Language list 200 OK on /utils/languages')

    return APIUtils.formatResponseObject(200, 'languageCounts', languageList)


@utils.route('/counts', methods=['GET'])
def totalCounts():
    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    totalResult = dbClient.fetchRowCounts()

    totalsSummary = APIUtils.formatTotals(totalResult)

    dbClient.closeSession()

    return APIUtils.formatResponseObject(200, 'totalCounts', totalsSummary)


@utils.route('/proxy', methods=['GET', 'POST', 'PUT', 'HEAD', 'OPTIONS'])
@cross_origin(origins=os.environ.get('API_PROXY_CORS_ALLOWED', '*'))
def getProxyResponse():
    proxyUrl = request.args.get('proxy_url')
    cleanUrl = unquote_plus(proxyUrl)
    urlParts = urlparse(cleanUrl)

    logger.info(f'Received {request.method} request to proxy url: {proxyUrl}')

    while True:
        headResp = requests.head(
            cleanUrl, headers={'User-agent': 'Mozilla/5.0'}
        )

        statusCode = headResp.status_code
        
        logger.info(f'HEAD response from {cleanUrl} returned status code {statusCode}')

        if statusCode in [200, 204]:
            break
        elif statusCode in [301, 302, 303, 307, 308]:
            cleanUrl = headResp.headers['Location']

            if cleanUrl[0] == '/':
                cleanUrl = '{}://{}{}'.format(
                    urlParts.scheme, urlParts.netloc, cleanUrl
                )
        else:
            logger.warn(f'Unable to proxy clean URL {cleanUrl}')
            cleanUrl = proxyUrl
            break


    resp = requests.request(
        method=request.method,
        url=cleanUrl,
        headers={k: v for (k, v) in request.headers if k != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False
    )

    headers = [
        (k, v) for (k, v) in resp.headers.items()
        if k.lower() not in EXCLUDED_HEADERS
    ]

    logger.info(f'Returning {request.method} response from {cleanUrl} with status code {resp.status_code}')

    return Response(resp.content, resp.status_code, headers)
