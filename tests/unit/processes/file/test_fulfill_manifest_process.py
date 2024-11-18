import pytest

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
    def test_process(self, mocker):
        class TestFulfill(FulfillURLManifestProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
                self.host = mocker.MagicMock(host='testHost')
                self.port = mocker.MagicMock(port='testPort')
                self.prefix = 'testPrefix'
                self.objKey = mocker.MagicMock(objKey='testKey')
                self.process = 'complete'
        
        return TestFulfill()

    def test_runProcess(self, test_process, mocker):
        run_mocks = mocker.patch.multiple(
            FulfillURLManifestProcess,
            fetch_and_update_manifests=mocker.DEFAULT,
        )

        test_process.runProcess()

        run_mocks['fetch_and_update_manifests'].assert_called_once()


    def test_fetch_and_update_manifests(self, test_process, mocker):
        mocker.patch.multiple(FulfillURLManifestProcess, update_metadata_object=mocker.DEFAULT)

        mock_timestamp = mocker.MagicMock(time_stamp='test_timestamp')
        
        test_process.fetch_and_update_manifests(mock_timestamp)

        test_process.s3_manager.load_batches.assert_called_once_with('testPrefix','test_aws_bucket')
        