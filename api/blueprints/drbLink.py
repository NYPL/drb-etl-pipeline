from flask import Blueprint, current_app, request
from ..db import DBClient
from ..utils import APIUtils
from ..validation_utils import is_valid_numeric_id
from app_logging import logger

link = Blueprint('link', __name__, url_prefix='/link')


@link.route('/<link_id>', methods=['GET'])
def get_link(link_id):
    logger.info(f'Getting link with id {link_id}')
    response_type = 'singleLink'

    if not is_valid_numeric_id(link_id):
        return APIUtils.formatResponseObject(400, response_type, { 'message': f'Link id {link_id} is invalid' })

    try:
        with DBClient(current_app.config['DB_CLIENT']) as db_client:
            link = db_client.fetchSingleLink(link_id)

            if not link:
                return APIUtils.formatResponseObject(
                    404, 
                    response_type,
                    { 'message': f'No link found with id {link_id}' }
                )
            
            return APIUtils.formatResponseObject(
                200, 
                response_type,
                APIUtils.formatLinkOutput(link, request=request)
            )
    except Exception as e:
        logger.error(e)
        return APIUtils.formatResponseObject(
            500, 
            response_type, 
            { 'message': f'Unable to get link with id {link_id}' }
        )
