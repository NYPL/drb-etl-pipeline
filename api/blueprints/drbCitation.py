from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

citation = Blueprint('citation', __name__, url_prefix='/citation')

citationSet = {'mla', 'apa', 'chicago'}

@citation.route('/<uuid>', methods=['GET'])
def citationFetch(uuid):
    logger.info('Fetching Identifier {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    searchParams = APIUtils.normalizeQueryParams(request.args)
    logger.debug(searchParams)

    citeFormats = request.args.get('format') #Default value is None if no arguments set
    formatList = citeFormats.split(',')
    formatListSet = set(formatList)
    logger.debug(formatListSet)

    if formatListSet.issubset(citationSet) == False:
        logger.warning('Page not found')
        return APIUtils.formatResponseObject(
                400, 'pageNotFound', {'message': 'Need to specify citation format'}
            )

    citationWork = dbClient.fetchSingleWork(uuid)
    
    outputCitations = {}

    for format in formatListSet:
        print("Do formatting here")
        if format == 'mla':
            newCite = mlaGenerator(citationWork)
        outputCitations[format] = newCite

    if citationWork:
        statusCode = 200
        responseBody = outputCitations
    else:
        statusCode = 404
        responseBody = {
            'message': f'Unable to locate work with UUID {uuid}'
        }

    logger.info(f'Citation Fetch {statusCode} on /citation/{uuid}')

    dbClient.closeSession()

    return APIUtils.formatResponseObject(
        statusCode, 'citation', responseBody
    )

def mlaGenerator(citationWork):
    if citationWork:
        return f'A FORMATTED CITATION {citationWork.title}'
    else:
        return None