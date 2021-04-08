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

    searchParams = APIUtils.normalizeQueryParams(request.args)
    showAll = searchParams.get('showAll', ['true'])[0].lower() != 'false'

    edition = dbClient.fetchSingleEdition(editionID)

    if not edition:
        logger.warning('Edition Fetch 404 on /edition/{}'.format(editionID))

        return APIUtils.formatResponseObject(
            404,
            'singleEdition',
            {'message': 'Unable to locate edition with id {}'.format(editionID)}
        )

    records = dbClient.fetchRecordsByUUID(edition.dcdw_uuids)

    logger.debug('Edition Fetch 200 on /edition/{}'.format(editionID))

    return APIUtils.formatResponseObject(
        200,
        'singleEdition',
        APIUtils.formatEditionOutput(edition, records=records, showAll=showAll)
    )