from flask import Blueprint, request, current_app
from ..utils import APIUtils
from logger import createLog
from functools import wraps
from botocore.exceptions import ClientError
from urllib.parse import urlparse

import requests
import argparse
import boto3
import json

logger = createLog(__name__)

s3 = Blueprint('s3', __name__, url_prefix='/s3')

@s3.route('/<bucket>', methods=['GET'])
def s3ObjectLinkFetch(bucket):

    logger.info(f'Fetching AWS S3 Object Link')

    searchParams = APIUtils.normalizeQueryParams(request.args)

    key = searchParams.get('key')[0]

    url = f'https://{bucket}.s3.amazonaws.com/{key}'

    response = requests.get(url)

    if response.status_code == 200:
        statusCode = 200
        responseBody = {
            'message': f'Object URL: {url}'
        }
    else:
        statusCode = response.status_code
        responseBody = {
            'message': f'URL does not exist {url}'
        }

    return APIUtils.formatResponseObject(
        statusCode, 's3ObjectLinkFetch', responseBody
     )

    # searchParams = APIUtils.normalizeQueryParams(request.args)

    # key = searchParams.get('key')[0]
    # logger.info(key)
    # logger.info(bucket)

    # parser = argparse.ArgumentParser()

    # logger.info(parser)

    # parser.add_argument(bucket, help=bucket)
    # parser.add_argument(key,help=key)
    # parser.add_argument("action", choices=("get"), help="get_object")
    
    # args = parser.parse_args()
    # logger.info(args)

    # s3_client = boto3.client("s3")
    # client_action = "get_object" #if args.action == "get" else None
    # url = generate_presigned_url(
    #     s3_client, client_action, {"Bucket": bucket, "Key": key}, 1000
    # )
    # logger.info(url)

    # logger.info("Using the Requests package to send a request to the URL.")
    # response = None
    # response = requests.get(url)
    # if args.action == "get":
    #     response = requests.get(url)

    # if response is not None:
    #     print("Got response:")
    #     print(f"Status: {response.status_code}")
        # dictResponse = json.loads(response.text)
        # linksResponse = dictResponse['links']
        # print(dictResponse)
        # print('\n')
        # print(linksResponse)
        # return response.text

# def generate_presigned_url(s3_client, client_method, method_parameters, expires_in):
#     """
#     Generate a presigned Amazon S3 URL that can be used to perform an action.

#     :param s3_client: A Boto3 Amazon S3 client.
#     :param client_method: The name of the client method that the URL performs.
#     :param method_parameters: The parameters of the specified client method.
#     :param expires_in: The number of seconds the presigned URL is valid for.
#     :return: The presigned URL.
#     """
#     try:
#         url = s3_client.generate_presigned_url(
#             ClientMethod=client_method, Params=method_parameters, ExpiresIn=expires_in
#         )
#         logger.info("Got presigned URL: %s", url)
#     except ClientError:
#         logger.exception(
#             "Couldn't get a presigned URL for client method '%s'.", client_method
#         )
#         raise
#     return url
