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
    def test_instance(self, mocker):
        class TestS3Process(S3Process):
            def __init__(self, process, customFile, ingestPeriod):
                self.bucket = 'testBucket'
        
        return TestS3Process('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def test_file_message(self):
        return """
            {
                "fileData": {
                    "fileURL": "testSourceURL",
                    "bucketPath": "testBucketPath.epub"
                }
            }
        """
    
    def test_run_process(self, test_instance, mocker):
        mock_process_files = mocker.patch.object(S3Process, 'process_files')
        mock_file_process = mocker.MagicMock()
        mock_process = mocker.patch('processes.file.s3_files.Process')
        mock_process.return_value = mock_file_process

        test_instance.runProcess()

        mock_process_files.assert_called_once
        assert mock_process.call_count == 4
        assert mock_file_process.start.call_count == 4
        assert mock_file_process.join.call_count == 4

    def test_process_files(self, test_file_message, mocker):
        mock_sleep = mocker.patch('processes.file.s3_files.sleep')

        mock_s3 = mocker.MagicMock()
        mock_s3_manager = mocker.patch('processes.file.s3_files.S3Manager')
        mock_s3_manager.return_value = mock_s3

        mock_rabbit_mq = mocker.MagicMock()
        mock_rabbit_mq_manager = mocker.patch('processes.file.s3_files.RabbitMQManager')
        mock_rabbit_mq_manager.return_value = mock_rabbit_mq
        mock_message_propse = mocker.MagicMock()
        mock_message_propse.delivery_tag = 'rabbitMQTag'
        mock_rabbit_mq.getMessageFromQueue.side_effect = [
            (mock_message_propse, {}, test_file_message),
            (None, None, None),
            (None, None, None),
            (None, None, None),
            (None, None, None)
        ]

        mock_get_file_contents = mocker.patch.object(S3Process, 'get_file_contents')
        mock_get_file_contents.return_value = 'testFileBytes'

        mock_generate_webpub = mocker.patch.object(S3Process, 'generate_webpub')
        mock_generate_webpub.return_value = 'testWebpubJson'

        S3Process.process_files()

        assert mock_rabbit_mq.getMessageFromQueue.call_count == 4
        mock_rabbit_mq.getMessageFromQueue.assert_called_with('test_file_queue')

        mock_sleep.assert_has_calls([
            mocker.call(30), mocker.call(60), mocker.call(90)
        ])

        mock_generate_webpub.assert_called_once_with('testBucketPath', 'test_aws_bucket')

        mock_s3.putObjectInBucket.assert_has_calls([
            mocker.call('testFileBytes', 'testBucketPath.epub', 'test_aws_bucket'),
            mocker.call('testWebpubJson', 'testBucketPath/manifest.json', 'test_aws_bucket')
        ])
        mock_rabbit_mq.acknowledgeMessageProcessed.assert_called_once_with('rabbitMQTag')

    def test_get_file_contents_success(self, test_instance, mocker):
        mock_get_request = mocker.patch.object(requests, 'get')
        mock_response = mocker.MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'e', b'p', b'u', b'b']
        mock_get_request.return_value = mock_response

        test_file = test_instance.get_file_contents('testURL')

        assert test_file == b'epub'
        mock_get_request.assert_called_once_with(
            'testURL',
            stream=True,
            timeout=15,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'}
        )
        
    def test_get_file_contents_error(self, test_instance, mocker):
        mock_get_request = mocker.patch.object(requests, 'get')
        mock_response = mocker.MagicMock()
        mock_response.raise_for_status.side_effect = Exception
        mock_get_request.return_value = mock_response

        with pytest.raises(Exception):
            test_instance.get_file_contents('testURL')

    def test_generate_webpub_success(self, mocker):
        mock_get_request = mocker.patch.object(requests, 'get')
        mock_response = mocker.MagicMock(content='testWebpub')
        mock_get_request.return_value = mock_response

        test_webpub = S3Process.generate_webpub('testRoot', 'testBucket')

        assert test_webpub == 'testWebpub'

        mock_get_request.assert_called_once_with(
            'test_conversion_url/api/https%3A%2F%2FtestBucket.s3.amazonaws.com%2FtestRoot%2FMETA-INF%2Fcontainer.xml',
            timeout=15
        )

    def test_generate_webpub_error(self, mocker):
        mock_get_request = mocker.patch.object(requests, 'get')
        mock_response = mocker.MagicMock(content='testWebpub')
        mock_response.raise_for_status.side_effect = Exception
        mock_get_request.return_value = mock_response

        with pytest.raises(Exception):
            S3Process.generate_webpub('testRoot', 'testBucket')

        mock_get_request.assert_called_once_with(
            'test_conversion_url/api/https%3A%2F%2FtestBucket.s3.amazonaws.com%2FtestRoot%2FMETA-INF%2Fcontainer.xml',
            timeout=15
        )
