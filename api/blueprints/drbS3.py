from flask import Blueprint, request, current_app
from ..utils import APIUtils
from logger import createLog
from functools import wraps
from botocore.exceptions import ClientError
from urllib.parse import urlparse

import requests
import argparse
import boto3

logger = createLog(__name__)

s3 = Blueprint('s3', __name__, url_prefix='/s3')

@s3.route('/<bucket>', methods=['GET'])
def s3ObjectLinkFetch(bucket):

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
