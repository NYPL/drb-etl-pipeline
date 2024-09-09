import pytest
import boto3
import os

from load_env import load_env_file
from processes import ClassifyProcess
from managers import DBManager
from model import Record

class test_classify_process:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return ClassifyProcess()
        # TODO: Run with custom StartDateTime to only classify records made during the test

    def test_run_process(self, test_instance: ClassifyProcess):
        s3_endpoint = os.environ.get("S3_ENDPOINT_URL")
        s3_client_local = boto3.client("s3", endpoint_url=s3_endpoint)
        bucket_name_local = 'drb-files=local'
        manifests = None #TODO: load manifests in from a test file?
        for manifest in manifests:
            s3_client_local.put_object(Body=manifest, Bucket=bucket_name_local, Key=manifests/) # TODO: name


        dbManager = DBManager(
            user=os.environ.get('POSTGRES_USER', None),
            pswd=os.environ.get('POSTGRES_PSWD', None),
            host=os.environ.get('POSTGRES_HOST', None),
            port=os.environ.get('POSTGRES_PORT', None),
            db=os.environ.get('POSTGRES_NAME', None)
         )

        dbManager.generateEngine()

        dbManager.createSession()

        # Query for title we attempted to process with Classify
        # assert that at least the number of ingested titles is there
        # assert that at least the standing number of clustered files is there

        dbManager.closeConnection()

        for manifest in manifests:
            s3_client_local.delete_object(Bucket=bucket_name_local, Key=manifests) # TODO: real key
