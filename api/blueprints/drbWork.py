from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

work = Blueprint('work', __name__, url_prefix='/work')


@work.route('/<uuid>', methods=['GET'])
def workFetch(uuid):
    logger.info('Fetching Work {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    searchParams = APIUtils.normalizeQueryParams(request.args)
    showAll = searchParams.get('showAll', ['true'])[0].lower() != 'false'
    readerVersion = searchParams.get('readerVersion', [None])[0]\
        or current_app.config['READER_VERSION']

    work = dbClient.fetchSingleWork(uuid)

    if work:
        statusCode = 200
        responseBody = APIUtils.formatWorkOutput(work, None, showAll=showAll, reader=readerVersion)
        
    else:
        statusCode = 404
        responseBody = {
            'message': 'Unable to locate work with UUID {}'.format(uuid)
        }

    logger.warning('Work Fetch {} on /work/{}'.format(statusCode, uuid))

    dbClient.closeSession()

    return APIUtils.formatResponseObject(
        statusCode, 'singleWork', responseBody
    )
