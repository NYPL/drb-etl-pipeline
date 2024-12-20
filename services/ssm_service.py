import os
import boto3
from typing import Optional

from logger import create_log

logger = create_log(__name__)

def _create_ssm_client():
    return boto3.client(
            'ssm',
            aws_access_key_id=os.environ.get('AWS_ACCESS', None),
            aws_secret_access_key=os.environ.get('AWS_SECRET', None),
            region_name=os.environ.get('AWS_REGION', None)
    )

ssm_client = None

def _get_or_create_ssm_client():
    if ssm_client is not None:
        return ssm_client
    ssm_client = _create_ssm_client()
    return ssm_client

def get_parameter(parameter_name: str) -> Optional[dict]:
    try:
        response = _get_or_create_ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        return response['Parameter']['Value']

    except Exception as err:
        logger.exception(f"Parameter store retrieval for {parameter_name} failed")
        return None
