from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

citation = Blueprint('citation', __name__, url_prefix='/citation')

uuidList = ['82427887-eed1-4ca5-8797-622c2c428809','1e5afa01-d854-49e3-bde3-4c93713fe878',
            'ecfcd12b-537f-4517-aa48-620a9eac6477','7279ba7d-d6c8-4dca-9847-9576df52f058',
            '1b628ab7-5f4b-46ff-9ab4-5493eec456e9','e3190e24-0de5-4858-9eb1-1670369fcfc6',
            '4e9d513e-ae38-4590-b10f-99eaea4ce65a','586c8728-3bb2-4415-8e78-71cab7a76122',
            '2264e2ac-061e-47f7-96dc-f37dfd013d31']

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