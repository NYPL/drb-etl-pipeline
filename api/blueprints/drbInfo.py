from flask import Blueprint, jsonify
import os

from logger import createLog

logger = createLog(__name__)


info = Blueprint('info', __name__, url_prefix='/')

@info.route('/', methods=['GET'])
def apiInfo():
    logger.debug('Status check 200 OK on /')

    return (
        jsonify({'environment': os.environ['ENVIRONMENT'], 'status': 'RUNNING'}),
        200
    )