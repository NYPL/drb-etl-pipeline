import os
import boto3
from typing import Optional

from logger import create_log

logger = create_log(__name__)

ssm_client = boto3.client(
            'ssm',
            aws_access_key_id=os.environ.get('AWS_ACCESS', None),
            aws_secret_access_key=os.environ.get('AWS_SECRET', None),
            region_name=os.environ.get('AWS_REGION', None)
        )

def get_parameter(parameter_name: str) -> Optional[dict]:
    try:
        response = ssm_client.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        return response

    except Exception as err:
        logger.exception(f"Parameter store retrieval for {parameter_name} failed")
        return None
