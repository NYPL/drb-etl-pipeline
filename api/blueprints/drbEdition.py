from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

edition = Blueprint('edition', __name__, url_prefix='/edition')


@edition.route('/<editionID>', methods=['GET'])
def editionFetch(editionID):
    logger.info('Fetching Edition #{}'.format(editionID))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    searchParams = APIUtils.normalizeQueryParams(request.args)
    showAll = searchParams.get('showAll', ['true'])[0].lower() != 'false'
    readerVersion = searchParams.get(
        'readerVersion', current_app.config['READER_VERSION']
    )

    edition = dbClient.fetchSingleEdition(editionID)

    if edition:
        statusCode = 200
        records = dbClient.fetchRecordsByUUID(edition.dcdw_uuids)
        responseBody = APIUtils.formatEditionOutput(
            edition, records=records, showAll=showAll, reader=readerVersion
        )
    else:
        statusCode = 404
        responseBody = {
            'message': 'Unable to locate edition with id {}'.format(editionID)
        }

    logger.debug(
        'Edition Fetch {} on /edition/{}'.format(statusCode, editionID)
    )

    dbClient.closeSession()

    return APIUtils.formatResponseObject(
        statusCode, 'singleEdition', responseBody
    )
