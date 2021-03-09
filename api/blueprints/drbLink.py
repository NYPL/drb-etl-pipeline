from flask import Blueprint, request, current_app
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

link = Blueprint('link', __name__, url_prefix='/link')

@link.route('/<linkID>', methods=['GET'])
def linkFetch(linkID):
    logger.info('Fetching Link #{}'.format(linkID))

    dbClient = DBClient(current_app.config['DB_CLIENT'])

    link = dbClient.fetchSingleLink(linkID)

    if link:
        logger.debug('Link Fetch 200 on /link/{}'.format(linkID))

        return APIUtils.formatResponseObject(
            200, 'singleLink', APIUtils.formatLinkOutput(link)
        )
    else:
        logger.warning('Link Fetch 404 on /link/{}'.format(linkID))

        return APIUtils.formatResponseObject(
            404, 'singleLink', {'message': 'Unable to locate link #{}'.format(linkID)}
        )