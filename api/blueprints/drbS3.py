from flask import Blueprint, request, current_app
from ..utils import APIUtils
from logger import createLog
from functools import wraps
from botocore.exceptions import ClientError
from urllib.parse import urlparse

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
    url = generate_presigned_url(
        s3_client, client_action, {"Bucket": bucket, "Key": key}, 1000
    )
    logger.info(url)

    return APIUtils.formatResponseObject(
        200, 's3ObjectLinkFetch', {'message': f'{url}'}
     )

def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
    """
    Generate a presigned Amazon S3 URL that can be used to perform an action.

    :param s3_client: A Boto3 Amazon S3 client.
    :param client_method: The name of the client method that the URL performs.
    :param method_parameters: The parameters of the specified client method.
    :param expires_in: The number of seconds the presigned URL is valid for.
    :return: The presigned URL.
    """
    try:
        url = s3_client.generate_presigned_url(
            ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
        )
        logger.info("Got presigned URL: %s", url)
    except ClientError:
        logger.exception(
            "Couldn't get a presigned URL for client method '%s'.", client_method
        )
        raise
    return url
