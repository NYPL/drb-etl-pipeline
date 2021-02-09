from flask import (
    Blueprint, request, session, url_for, redirect, current_app, jsonify
)
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

work = Blueprint('work', __name__, url_prefix='/work')

@work.route('/<uuid>', methods=['GET'])
def workFetch(uuid):
    logger.info('Fetching Work {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])

    searchParams = APIUtils.normalizeQueryParams(request.args)
    showAll = searchParams.get('showAll', ['true'])[0].lower() != 'false'

    work = dbClient.fetchSingleWork(uuid)

    if work:
        logger.debug('Work Fetch 200 on /work/{}'.format(uuid))

        return APIUtils.formatResponseObject(
            200,
            'singleWork',
            APIUtils.formatWorkOutput(work, showAll=showAll)
        )
    else:
        logger.warning('Work Fetch 404 on /work/{}'.format(uuid))

        return APIUtils.formatResponseObject(
            404,
            'singleWork',
            {'message': 'Unable to locate work with UUID {}'.format(uuid)}
        )