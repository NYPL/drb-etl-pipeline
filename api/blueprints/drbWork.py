from flask import (
    Blueprint, request, session, url_for, redirect, current_app, jsonify
)
from ..db import DBClient
from ..utils import APIUtils

work = Blueprint('work', __name__, url_prefix='/work')

@work.route('/<uuid>', methods=['GET'])
def workFetch(uuid):
    dbClient = DBClient(current_app.config['DB_CLIENT'])

    searchParams = APIUtils.normalizeQueryParams(request.args)
    showAll = False if searchParams.get('showAll', ['true'])[0].lower() == 'false' else True

    work = dbClient.fetchSingleWork(uuid)

    if work:
        return APIUtils.formatResponseObject(
            200,
            'singleWork',
            APIUtils.formatWorkOutput(work, showAll=showAll)
        )
    else:
        return APIUtils.formatResponseObject(
            404,
            'singleWork',
            {'message': 'Unable to locate work with UUID {}'.format(uuid)}
        )