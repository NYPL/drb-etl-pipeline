import pytest
import requests

from tests.helper import TestHelpers
from processes import S3Process


class TestS3Process:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestS3Process(S3Process):
            def __init__(self, process, customFile, ingestPeriod):
                self.bucket = 'testBucket'
        
        return TestS3Process('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testFile(self):
        return """
        {
            "fileData": {
                "fileURL": "testSourceURL",
                "bucketPath": "testBucketPath.epub"
            }
        }
        """
    
    def test_runProcess(self, testInstance, mocker):
        mockReceive = mocker.patch.object(S3Process, 'receiveAndProcessMessages')
        mockSave = mocker.patch.object(S3Process, 'saveRecords')
        mockCommit = mocker.patch.object(S3Process, 'commitChanges')

        testInstance.runProcess()

        mockReceive.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_receiveAndProcessMessages(self, testInstance, mocker):
        mockProc = mocker.MagicMock()
        mockProcess = mocker.patch('processes.s3Files.Process')
        mockProcess.return_value = mockProc

        testInstance.receiveAndProcessMessages()

        assert mockProcess.call_count == 4
        assert mockProc.start.call_count == 4
        assert mockProc.join.call_count == 4

    def test_storeFilesInS3(self, testFile, mocker):
        mockSleep = mocker.patch('processes.s3Files.sleep')

        mockS3 = mocker.MagicMock()
        mockS3Manager = mocker.patch('processes.s3Files.S3Manager')
        mockS3Manager.return_value = mockS3

        mockRabbit = mocker.MagicMock()
        mockRabbitManager = mocker.patch('processes.s3Files.RabbitMQManager')
        mockRabbitManager.return_value = mockRabbit

        mockProps = mocker.MagicMock()
        mockProps.delivery_tag = 'rabbitMQTag'
        mockRabbit.getMessageFromQueue.side_effect = [
            (mockProps, {}, testFile),
            (None, None, None),
            (None, None, None),
            (None, None, None),
            (None, None, None)
        ]

        mockGet = mocker.patch.object(S3Process, 'getFileContents')
        mockGet.return_value = 'testFileBytes'

        mockGenerateWebpub = mocker.patch.object(S3Process, 'generateWebpub')
        mockGenerateWebpub.return_value = 'testWebpubJson'

        S3Process.storeFilesInS3()

        assert mockRabbit.getMessageFromQueue.call_count == 5
        mockRabbit.getMessageFromQueue.assert_called_with('test_file_queue')

        mockSleep.assert_has_calls([
            mocker.call(30), mocker.call(60), mocker.call(90)
        ])

        mockGenerateWebpub.assert_called_once_with('test_conversion_url', 'testBucketPath', 'test_aws_bucket')

        mockS3.putObjectInBucket.assert_has_calls([
            mocker.call('testFileBytes', 'testBucketPath.epub', 'test_aws_bucket'),
            mocker.call('testWebpubJson', 'testBucketPath/manifest.json', 'test_aws_bucket')
        ])
        mockRabbit.acknowledgeMessageProcessed.assert_called_once_with('rabbitMQTag')

    def test_getFileContents_success(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.iter_content.return_value = [b'e', b'p', b'u', b'b']
        mockGet.return_value = mockResp

        testEpubFile = testInstance.getFileContents('testURL')

        assert testEpubFile == b'epub'
        mockGet.assert_called_once_with(
            'testURL',
            stream=True,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'}
        )
        
    def test_getFileContents_error(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testInstance.getFileContents('testURL')

    def test_generateWebpub_success(self, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock(content='testWebpub')
        mockGet.return_value = mockResp

        testWebpub = S3Process.generateWebpub('converterURL', 'testRoot', 'testBucket')

        assert testWebpub == 'testWebpub'

        mockGet.assert_called_once_with(
            'converterURL/api/https%3A%2F%2FtestBucket.s3.amazonaws.com%2FtestRoot%2FMETA-INF%2Fcontainer.xml',
            timeout=15
        )

    def test_generateWebpub_error(self, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock(content='testWebpub')
        mockResp.raise_for_status.side_effect = Exception
        mockGet.return_value = mockResp

        testWebpub = S3Process.generateWebpub('converterURL', 'testRoot', 'testBucket')

        assert testWebpub == None

        mockGet.assert_called_once_with(
            'converterURL/api/https%3A%2F%2FtestBucket.s3.amazonaws.com%2FtestRoot%2FMETA-INF%2Fcontainer.xml',
            timeout=15
        )
