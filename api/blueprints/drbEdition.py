from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

edition = Blueprint('edition', __name__, url_prefix='/edition')
RESPONSE_TYPE = 'singleEdition'


@edition.route('/<editionID>', methods=['GET'])
def editionFetch(editionID):
    logger.info('Fetching Edition #{}'.format(editionID))

    try: 
        with DBClient(current_app.config['DB_CLIENT']) as dbClient:
            searchParams = APIUtils.normalizeQueryParams(request.args)
            terms = { param: APIUtils.extractParamPairs(param, searchParams) for param in ['filter'] }
            showAll = searchParams.get('showAll', ['true'])[0].lower() != 'false'
            readerVersion = searchParams.get('readerVersion', [None])[0]\
                or current_app.config['READER_VERSION']
            filteredFormats = APIUtils.formatFilters(terms)

            if not isValidEditionID(editionID):
                return APIUtils.formatResponseObject(400, RESPONSE_TYPE, { 'message': 'Edition id {} is invalid'.format(editionID) })

            edition = dbClient.fetchSingleEdition(editionID)

            if not edition:
                return APIUtils.formatResponseObject(404, RESPONSE_TYPE, { 'message': 'Unable to locate edition with id {}'.format(editionID) })

            records = dbClient.fetchRecordsByUUID(edition.dcdw_uuids)

            return APIUtils.formatResponseObject(
                200,
                RESPONSE_TYPE, 
                APIUtils.formatEditionOutput(
                    edition, request=request, records=records, dbClient=dbClient, showAll=showAll, formats=filteredFormats, reader=readerVersion
                )
            )
    except Exception as e: 
        logger.error(e)
        return APIUtils.formatResponseObject(500, RESPONSE_TYPE, { 'message': 'Unable to fetch edition with id {}'.format(editionID) })


def isValidEditionID(editionID) -> bool:
    return isinstance(editionID, int) or (isinstance(editionID, str) and editionID.isdigit())
