from flask import Blueprint, current_app, request
from ..db import DBClient
from ..utils import APIUtils
from logger import createLog

logger = createLog(__name__)

link = Blueprint('link', __name__, url_prefix='/link')
RESPONSE_TYPE = 'singleLink'

@link.route('/<link_id>', methods=['GET'])
def get_link(link_id):
    logger.info(f'Getting link with id {link_id}')

    try:
        with DBClient(current_app.config['DB_CLIENT']) as db_client:
            link = db_client.fetchSingleLink(link_id)

            if not link:
                return APIUtils.formatResponseObject(
                    404, 
                    RESPONSE_TYPE, 
                    { 'message': f'No link found with id {link_id}' }
                )
            
            return APIUtils.formatResponseObject(
                200, 
                RESPONSE_TYPE, 
                APIUtils.formatLinkOutput(link, request=request)
            )
    except Exception as e:
        logger.error(e)
        return APIUtils.formatResponseObject(
            500, 
            RESPONSE_TYPE, 
            { 'message': f'Unable to get link with id {link_id}' }
        )
