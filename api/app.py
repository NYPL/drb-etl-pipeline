from elasticsearch.exceptions import RequestError
from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
import json
import os
from sqlalchemy.exc import DataError
from waitress import serve

from logger import createLog
from .blueprints import (
    search, work, info, edition, utils, link, opds, collection
)
from .utils import APIUtils

logger = createLog(__name__)


class FlaskAPI:
    def __init__(self, dbEngine, redisClient):
        self.app = Flask(__name__)
        CORS(self.app)
        Swagger(self.app, template=json.load(open('swagger.v4.json', 'r')))

        self.app.config['DB_CLIENT'] = dbEngine
        self.app.config['REDIS_CLIENT'] = redisClient

        self.app.config['READER_VERSION'] = os.environ['READER_VERSION']

        self.app.register_blueprint(info)
        self.app.register_blueprint(search)
        self.app.register_blueprint(work)
        self.app.register_blueprint(edition)
        self.app.register_blueprint(utils)
        self.app.register_blueprint(link)
        self.app.register_blueprint(opds)
        self.app.register_blueprint(collection)

    def run(self):
        if 'local' in os.environ['ENVIRONMENT']:
            logger.debug('Starting dev server on port 5000')

            self.app.config['ENV'] = 'development'
            self.app.config['DEBUG'] = True
            self.app.run()
        else:
            logger.debug('Starting production server on port 80')

            serve(self.app, host='0.0.0.0', port=80)

    def createErrorResponses(self):
        @self.app.errorhandler(404)
        def pageNotFound(error):
            logger.warning('Page not found')
            logger.debug(error)
            return APIUtils.formatResponseObject(
                404, 'pageNotFound', {'message': 'Request page does not exist'}
            )

        @self.app.errorhandler(DataError)
        def dataError(error):
            logger.warning('Internal SQLAlchemy error')
            logger.debug(error)
            return APIUtils.formatResponseObject(
                500, 'dataError',
                {'message': 'Encountered fatal database error'}
            )

        @self.app.errorhandler(RequestError)
        def requestError(error):
            logger.warning('Invalid parameter passed to ElasticSearch')
            logger.debug(error)
            return APIUtils.formatResponseObject(
                400, 'requestError',
                {'message': error.info['error']['root_cause'][0]['reason']}
            )
