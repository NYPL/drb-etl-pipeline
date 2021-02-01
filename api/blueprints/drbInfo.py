from flask import Blueprint, jsonify
import os

info = Blueprint('info', __name__, url_prefix='/')

@info.route('/', methods=['GET'])
def apiInfo():
    return (
        jsonify({'environment': os.environ['ENVIRONMENT'], 'status': 'RUNNING'}),
        200
    )