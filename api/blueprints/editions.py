from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from ..validation_utils import is_valid_numeric_id
from logger import createLog

logger = createLog(__name__)

edition = Blueprint('edition', __name__, url_prefix='/edition')


@edition.route('/<editionID>', methods=['GET'])
def get_edition(edition_id):
    logger.info(f'Getting edition with id {edition_id}')
    response_type = 'singleEdition'

    try: 
        with DBClient(current_app.config['DB_CLIENT']) as db_client:
            search_params = APIUtils.normalizeQueryParams(request.args)
            terms = { param: APIUtils.extractParamPairs(param, search_params) for param in ['filter'] }
            show_all = search_params.get('showAll', ['true'])[0].lower() != 'false'
            reader_version = search_params.get('readerVersion', [None])[0] or current_app.config['READER_VERSION']
            filtered_formats = APIUtils.formatFilters(terms)

            if not is_valid_numeric_id(edition_id):
                return APIUtils.formatResponseObject(400, response_type, { 'message': f'Edition id {edition_id} is invalid' })

            edition = db_client.fetchSingleEdition(edition_id)

            if not edition:
                return APIUtils.formatResponseObject(404, response_type, { 'message': f'No edition found with id {edition_id}' })

            records = db_client.fetchRecordsByUUID(edition.dcdw_uuids)

            return APIUtils.formatResponseObject(
                200,
                response_type, 
                APIUtils.formatEditionOutput(
                    edition, request=request, records=records, dbClient=db_client, showAll=show_all, formats=filtered_formats, reader=reader_version
                )
            )
    except Exception as e: 
        logger.error(e)
        return APIUtils.formatResponseObject(500, response_type, { 'message': f'Unable to get edition with id {edition_id}' })
