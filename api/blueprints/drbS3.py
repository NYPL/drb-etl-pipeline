from flask import Blueprint, request, current_app
from base64 import b64decode
from ..db import DBClient
from ..utils import APIUtils
from functools import wraps
from logger import createLog
from functools import wraps

import requests
import argparse
import boto3

logger = createLog(__name__)

s3 = Blueprint('s3', __name__, url_prefix='/s3')

def validateToken(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        logger.debug(request.headers)

        headers = {k.lower(): v for k, v in request.headers.items()}

        try:
            _, loginPair = headers['authorization'].split(' ')
            loginBytes = loginPair.encode('utf-8')
            user, password = b64decode(loginBytes).decode('utf-8').split(':')
        except KeyError:
            return APIUtils.formatResponseObject(
                403, 'authResponse', {'message': 'user/password not provided'}
            )

        dbClient = DBClient(current_app.config['DB_CLIENT'])
        dbClient.createSession()

        user = dbClient.fetchUser(user)

        if not user or APIUtils.validatePassword(password, user.password, user.salt) is False:
            return APIUtils.formatResponseObject(
                401, 'authResponse', {'message': 'invalid user/password'}
            )

        dbClient.closeSession()

        kwargs['user'] = user.user

        return func(*args, **kwargs)

    return decorator


@s3.route('/<bucket>', methods=['GET'])
@validateToken
def s3ObjectLinkFetch(bucket,user=None):

    logger.info(f'Fetching AWS S3 Object Link')

    searchParams = APIUtils.normalizeQueryParams(request.args)

    key = searchParams.get('key')[0]

    logger.info(f'Key: {key}')
    logger.info(f'Bucket: {bucket}')

    parser = argparse.ArgumentParser()

    parser.add_argument(bucket, help=bucket)
    parser.add_argument(key, help=key)

    logger.info(parser)

    s3_client = boto3.client("s3")
    client_action = "get_object"
    url = APIUtils.generate_presigned_url(
        s3_client, client_action, {"Bucket": bucket, "Key": key}, 1000
    )
    logger.info(url)

    response = requests.get(url)

    if response.status_code == 200:
        return APIUtils.formatResponseObject(
        200, 's3ObjectLinkFetch', {'message': f'{url}'}
     )
    else:
        return APIUtils.formatResponseObject(
        response.status_code, 's3ObjectLinkFetch', {'Bucket/Key does not exist': f'{url}'}
     )
