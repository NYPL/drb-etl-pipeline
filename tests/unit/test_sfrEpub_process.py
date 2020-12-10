import pytest
import requests

from tests.helper import TestHelpers
from processes import EpubProcess


class TestEpubProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestEpubProcess(EpubProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.bucket = 'testBucket'
        
        return TestEpubProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testFile(self):
        return """
        {
            "epubData": {
                "epubURL": "testSourceURL",
                "bucketPath": "testBucketPath"
            }
        }
        """
    
    def test_runProcess(self, testInstance, mocker):
        mockReceive = mocker.patch.object(EpubProcess, 'receiveAndProcessMessages')
        mockSave = mocker.patch.object(EpubProcess, 'saveRecords')
        mockCommit = mocker.patch.object(EpubProcess, 'commitChanges')

        testInstance.runProcess()

        mockReceive.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_receiveAndProcessMessages(self, testInstance, mocker):
        mockSleep = mocker.patch('processes.sfrEpub.sleep')
        mockQueueGet = mocker.patch.object(EpubProcess, 'getMessageFromQueue')
        mockProps = mocker.MagicMock()
        mockProps.delivery_tag = 'rabbitMQTag'
        mockQueueGet.side_effect = [
            (mockProps, {}, 'epub_record'),
            (None, None, None),
            (None, None, None),
            (None, None, None),
            (None, None, None)
        ]
        mockStore = mocker.patch.object(EpubProcess, 'storeEpubFile')
        mockAcknowledge = mocker.patch.object(EpubProcess, 'acknowledgeMessageProcessed')

        testInstance.receiveAndProcessMessages()

        assert mockQueueGet.call_count == 5
        mockQueueGet.assert_called_with('test_epub_queue')

        mockSleep.assert_has_calls([
            mocker.call(30), mocker.call(60), mocker.call(90)
        ])

        mockStore.assert_called_once_with('epub_record')
        mockAcknowledge.assert_called_once_with('rabbitMQTag')

    def test_storeEpubFile(self, testInstance, testFile, mocker):
        mockGetContents = mocker.patch.object(EpubProcess, 'getFileContents')
        mockGetContents.return_value = 'epubBinary'
        mockPutInS3 = mocker.patch.object(EpubProcess, 'putObjectInBucket')

        testInstance.storeEpubFile(testFile)

        mockGetContents.assert_called_once_with('testSourceURL')
        mockPutInS3.assert_called_once_with('epubBinary', 'testBucketPath', 'testBucket')

    def test_getFileContents_success(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.content = 'epubBinary'
        mockGet.return_value = mockResp

        testEpubFile = testInstance.getFileContents('testURL')

        assert testEpubFile == 'epubBinary'
        mockGet.assert_called_once_with('testURL')
        
    def test_getFileContents_error(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testEpubFile = testInstance.getFileContents('testURL')
            mockGet.assert_called_once_with('testURL')
