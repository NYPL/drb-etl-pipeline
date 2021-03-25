from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
import json
import os
from waitress import serve

from logger import createLog
from .blueprints import search, work, info, edition, utils, link

logger = createLog(__name__)


class FlaskAPI:
    def __init__(self, client, dbEngine):
        self.app = Flask(__name__)
        CORS(self.app)
        Swagger(self.app, template=json.load(open('swagger.v4.json', 'r')))
        self.app.config['ES_CLIENT'] = client
        self.app.config['DB_CLIENT'] = dbEngine

        self.app.register_blueprint(info)
        self.app.register_blueprint(search)
        self.app.register_blueprint(work)
        self.app.register_blueprint(edition)
        self.app.register_blueprint(utils)
        self.app.register_blueprint(link)

    def run(self):
        if 'local' in os.environ['ENVIRONMENT']:
            logger.debug('Starting dev server on port 5000')

            self.app.config['ENV'] = 'development'
            self.app.config['DEBUG'] = True
            self.app.run()
        else:
            logger.debug('Starting production server on port 80')

            serve(self.app, host='0.0.0.0', port=80)
