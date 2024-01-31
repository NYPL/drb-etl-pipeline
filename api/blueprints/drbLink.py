from flask import Blueprint, current_app, request
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

link = Blueprint('link', __name__, url_prefix='/link')

@link.route('/<linkID>', methods=['GET'])
def linkFetch(linkID):
    logger.info('Fetching Link #{}'.format(linkID))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    link = dbClient.fetchSingleLink(linkID)

    if link:
        statusCode = 200
        responseObject = APIUtils.formatLinkOutput(link, request=request)
    else:
        statusCode = 404
        responseObject = {'message': 'Unable to locate link #{}'.format(linkID)}

    logger.debug('Link Fetch 200 on /link/{}'.format(linkID))

    dbClient.closeSession()

    return APIUtils.formatResponseObject(statusCode, 'singleLink', responseObject)
