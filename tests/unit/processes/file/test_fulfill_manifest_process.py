import pytest

from mappings.base_mapping import MappingError
from processes.file.fulfill_url_manifest import FulfillURLManifestProcess
from tests.helper import TestHelpers

class TestUofMProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestFulfill(FulfillURLManifestProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3Client = mocker.MagicMock(s3Client='testS3Client')
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
                self.host = mocker.MagicMock(host='testHost')
                self.port = mocker.MagicMock(port='testPort')
                self.prefix = 'testPrefix'
                self.objKey = mocker.MagicMock(objKey='testKey')
                self.process = 'complete'
        
        return TestFulfill()

    def test_runProcess(self, testProcess, mocker):
        runMocks = mocker.patch.multiple(
            FulfillURLManifestProcess,
            fetch_and_update_manifests=mocker.DEFAULT,
        )

        testProcess.runProcess()

        runMocks['fetch_and_update_manifests'].assert_called_once()


    def test_fetch_and_update_manifests(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(FulfillURLManifestProcess,
            load_batches=mocker.DEFAULT,
            getObjectFromBucket=mocker.DEFAULT,
            update_metadata_object=mocker.DEFAULT
        )

        mockPrefix = mocker.MagicMock(prefix='testPrefix')
        mockTimeStamp = mocker.MagicMock(timeStamp='testTimeStamp')
        
        testProcess.fetch_and_update_manifests(mockTimeStamp)

        processMocks['load_batches'].assert_called_once_with('testPrefix','test_aws_bucket')
        