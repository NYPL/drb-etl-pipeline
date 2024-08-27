import pytest
import boto3
import json
import os
from load_env import load_env_file
from processes import UofMProcess
from managers import DBManager
from model import Record

class TestUofMProcess:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return UofMProcess('complete', None, None, None, None, None, [])
    
    @pytest.fixture
    def test_instance_QA(self):
        load_env_file('local-qa', file_string='config/local-qa.yaml')
    
    def test_runProcess(self, test_instance_QA, test_instance: UofMProcess):
        # Run process for only 1 record
        # TODO - create S3 client and upload PDF

        s3_client = boto3.client("s3")

        s3_endpoint = os.environ.get("S3_ENDPOINT_URL")
        s3_client_local = boto3.client("s3", endpoint_url=s3_endpoint)

        bucketNameQA = 'drb-files-qa'
        metadataObject = s3_client.get_object(Bucket=bucketNameQA, Key='manifests/UofM/0472030132.json')
        bucketNameLocal = 'drb-files-local'
        manifestJSON = json.loads(metadataObject['Body'].read().decode("utf-8"))
        manifest = json.dumps(manifestJSON, ensure_ascii = False)
        s3_client_local.put_object(Body=manifest, Bucket=bucketNameLocal, Key='manifests/UofM/0472030132.json')
        
        test_instance.runProcess()
        
        # TODO - connect to S3 and get the PDF manifest
        # assert the PDF manifest is stored
        localManifest = s3_client_local.get_object(Bucket=bucketNameLocal, Key='manifests/UofM/0472030132.json')
        assert localManifest is not None

        # TODO - create a database session/client 
        # assert DCDW record exists
        # assert the rights are correct
        # assert the link string is correct
        dbManager = DBManager(
            user=os.environ.get('POSTGRES_USER', None),
            pswd=os.environ.get('POSTGRES_PSWD', None),
            host=os.environ.get('POSTGRES_HOST', None),
            port=os.environ.get('POSTGRES_PORT', None),
            db=os.environ.get('POSTGRES_NAME', None)
         )

        dbManager.generateEngine()

        dbManager.createSession()

        recordExample = dbManager.session.query(Record) \
            .filter(Record.title == 'Intermediate reading practices : building reading and vocabulary skills ').first()  

        assert recordExample != None
        assert recordExample.rights == 'UofM|in_copyright||In Copyright|'

        # TODO SFR-2150 - kickoff oclc process when it's ready
        # assert DCDW oclc records exist

        # TODO - kickoff clustering process
        # assert works, edition, items, links data exist

        # TODO - setup elastic search client
        # assert search document(s) exist in elastic search

        # TODO - delete data in S3, postgres, and elastic search
        s3_client_local.delete_object(Bucket=bucketNameLocal, Key='manifests/UofM/0472030132.json')
