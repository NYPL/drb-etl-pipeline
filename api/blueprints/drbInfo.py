from flask import Blueprint, url_for, redirect

from logger import createLog

logger = createLog(__name__)


info = Blueprint('info', __name__, url_prefix='/')

@info.route('/', methods=['GET'])
def apiInfo():
    logger.debug('Status check 200 OK on /')

    return redirect(url_for('flasgger.apidocs'))