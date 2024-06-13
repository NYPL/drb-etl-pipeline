import pytest

from mappings.core import MappingError
from processes.fulfillURLManifest import FulfillProcess
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
        class TestFulfill(FulfillProcess):
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
            FulfillProcess,
            getManifests=mocker.DEFAULT,
        )

        testProcess.runProcess()

        runMocks['getManifests'].assert_called_once()


    def test_getManifests_success(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(FulfillProcess,
            load_batches=mocker.DEFAULT,
            getObjectFromBucket=mocker.DEFAULT,
            update_manifest=mocker.DEFAULT
        )

        mockPrefix = mocker.MagicMock(prefix='testPrefix')
        mockTimeStamp = mocker.MagicMock(timeStamp='testTimeStamp')
        
        testProcess.getManifests(mockTimeStamp)


        processMocks['load_batches'].assert_called_once_with('testPrefix','test_aws_bucket')
        