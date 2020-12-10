from elasticsearch_dsl import Search, Q
from flask import Flask, request, Response
from flask_cors import CORS
import os
from waitress import serve

from model import Work
from .blueprints import search, work


class FlaskAPI:
    def __init__(self, client, dbEngine):
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['ES_CLIENT'] = client
        self.app.config['DB_CLIENT'] = dbEngine

        self.app.register_blueprint(search)
        self.app.register_blueprint(work)

    def run(self):
        if os.environ['ENVIRONMENT'] == 'local':
            self.app.run()
        else:
            serve(self.app, host='0.0.0.0', port=5000)
