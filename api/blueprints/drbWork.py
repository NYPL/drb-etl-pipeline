from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

work = Blueprint('work', __name__, url_prefix='/work')

@work.route('/<uuid>', methods=['GET'])
def get_work(uuid):
    logger.info(f'Getting work with id {uuid}')
    reponse_type = 'singleWork'

    try: 
        with DBClient(current_app.config['DB_CLIENT']) as db_client:
            search_params = APIUtils.normalizeQueryParams(request.args)
            terms = { param: APIUtils.extractParamPairs(param, search_params) for param in ['filter'] }
            show_all = search_params.get('showAll', ['true'])[0].lower() != 'false'
            reader_version = search_params.get('readerVersion', [None])[0] or current_app.config['READER_VERSION']
            filtered_formats = APIUtils.formatFilters(terms)

            work = db_client.fetchSingleWork(uuid)

            if not work:
                return APIUtils.formatResponseObject(404, reponse_type, { 'message': f'No work found with id {uuid}' })

            return APIUtils.formatResponseObject(
                200, 
                reponse_type,
                APIUtils.formatWorkOutput(work, None, showAll=show_all,
                    request=request, dbClient=db_client, formats=filtered_formats, reader=reader_version
                )
            )
    except Exception as e:
        logger.error(e)
        return APIUtils.formatResponseObject(500, reponse_type, { 'message': f'Unable to get work with id {uuid}' })
