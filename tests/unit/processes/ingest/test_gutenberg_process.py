from datetime import datetime
import os
import pytest

from tests.helper import TestHelpers
from model import get_file_message
from processes import GutenbergProcess


class TestGutenbergProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestGutenbergProcess(GutenbergProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.constants = {}
                self.ingest_period = None
                self.ingestOffset = 0
                self.ingestLimit = 5000
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock()
                self.s3Bucket = os.environ['FILE_BUCKET']
                self.fileQueue = os.environ['FILE_QUEUE']
                self.fileRoute = os.environ['FILE_ROUTING_KEY']
                self.records = []
                self.rabbitmq_manager = mocker.MagicMock()
        
        return TestGutenbergProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testMetadataYAML(self):
        return {
            'covers': [
                {'cover_type': 'generated', 'image_path': 'images/cover.png'},
                {'cover_type': 'archival', 'image_path': 'images/cover.jpg'}
            ],
            'identifiers': {'gutenberg': '1'},
            'url': 'gutenberg.org/ebooks/1'
        }
    
    def test_runProcess_daily(self, testInstance, mocker):
        mockImport = mocker.patch.object(GutenbergProcess, 'importRDFRecords')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        testInstance.record_buffer.flush.assert_called_once()

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(GutenbergProcess, 'importRDFRecords')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once_with(fullImport=True)
        testInstance.record_buffer.flush.assert_called_once()

    def test_runProcess_custom(self, testInstance, mocker):
        mockImport = mocker.patch.object(GutenbergProcess, 'importRDFRecords')

        testInstance.process = 'custom'
        testInstance.ingest_period = 'testPeriod'
        testInstance.runProcess()

        mockImport.assert_called_once_with(startTimestamp='testPeriod')
        testInstance.record_buffer.flush.assert_called_once()

    def test_importRDFRecords_partial(self, testInstance, mocker):
        mockProcess = mocker.patch.object(GutenbergProcess, 'processGutenbergBatch')
        mockManager = mocker.MagicMock()
        mockManager.fetchGithubRepoBatch.side_effect = [True, False]
        mockManager.dataFiles = 'testDataFiles'
        mockManagerInit = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mockManagerInit.return_value = mockManager

        mockDateTime = mocker.patch('processes.ingest.gutenberg.datetime')
        mockDateTime.now.return_value.replace.return_value = datetime(1900, 1, 2, 12, 0, 0)
        
        testInstance.importRDFRecords()

        mockManagerInit.assert_called_once_with('DESC', 'PUSHED_AT', datetime(1900, 1, 1, 12, 0, 0), 100)
        mockProcess.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mockManager.fetchGithubRepoBatch.call_count == 2
        assert mockManager.fetchMetadataFilesForBatch.call_count == 2
        assert mockManager.resetBatch.call_count == 2

    def test_importRDFRecords_custom(self, testInstance, mocker):
        mockProcess = mocker.patch.object(GutenbergProcess, 'processGutenbergBatch')
        mockManager = mocker.MagicMock()
        mockManager.fetchGithubRepoBatch.side_effect = [True, False]
        mockManager.dataFiles = 'testDataFiles'
        mockManagerInit = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mockManagerInit.return_value = mockManager

        testInstance.importRDFRecords(startTimestamp='1900-01-01T12:00:00')

        mockManagerInit.assert_called_once_with('DESC', 'PUSHED_AT', datetime(1900, 1, 1, 12, 0, 0), 100)
        mockProcess.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mockManager.fetchGithubRepoBatch.call_count == 2
        assert mockManager.fetchMetadataFilesForBatch.call_count == 2
        assert mockManager.resetBatch.call_count == 2

    def test_importRDFRecords_complete(self, testInstance, mocker):
        mockProcess = mocker.patch.object(GutenbergProcess, 'processGutenbergBatch')
        mockManager = mocker.MagicMock()
        mockManager.fetchGithubRepoBatch.side_effect = [True, False]
        mockManager.dataFiles = 'testDataFiles'
        mockManagerInit = mocker.patch('processes.ingest.gutenberg.GutenbergManager')
        mockManagerInit.return_value = mockManager

        testInstance.importRDFRecords(fullImport=True)

        mockManagerInit.assert_called_once_with('ASC', 'CREATED_AT', None, 100)
        mockProcess.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mockManager.fetchGithubRepoBatch.call_count == 2
        assert mockManager.fetchMetadataFilesForBatch.call_count == 2
        assert mockManager.resetBatch.call_count == 2

    def test_processGutenbergBatch(self, testInstance, mocker):
        mockGutenbergRec = mocker.MagicMock(name='MockRecord', record=mocker.MagicMock(source_id=1))
        mockGutenbergInit = mocker.patch('processes.ingest.gutenberg.GutenbergMapping')
        mockGutenbergInit.return_value = mockGutenbergRec

        processMocks = mocker.patch.multiple(
            GutenbergProcess,
            storeEpubsInS3=mocker.DEFAULT,
            addCoverAndStoreInS3=mocker.DEFAULT,
        )

        processMocks['addCoverAndStoreInS3'].side_effect = [None, KeyError]

        testInstance.processGutenbergBatch([('rdf1', 'yaml1'), ('rdf2', 'yaml2')])

        mockGutenbergInit.assert_has_calls([
            mocker.call('rdf1', GutenbergProcess.GUTENBERG_NAMESPACES, {}),
            mocker.call('rdf2', GutenbergProcess.GUTENBERG_NAMESPACES, {})
        ])
        assert mockGutenbergRec.applyMapping.call_count == 2
        processMocks['storeEpubsInS3'].assert_has_calls([
            mocker.call(mockGutenbergRec), mocker.call(mockGutenbergRec)
        ])
        processMocks['addCoverAndStoreInS3'].assert_has_calls([
            mocker.call(mockGutenbergRec, 'yaml1'), mocker.call(mockGutenbergRec, 'yaml2')
        ])
        testInstance.record_buffer.add.assert_has_calls([
            mocker.call(mockGutenbergRec.record), mocker.call(mockGutenbergRec.record)
        ])

    def test_storeEpubsInS3(self, testInstance, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.record.has_part = [
            '1|gutenberg.org/ebook/1.epub.images|gutenberg|application/epub+zip|{"download": true}',
            '1|gutenberg.org/ebook/1.epub.images|gutenberg|application/epub|{"download": false}',
            '2|gutenberg.org/ebook/2.epub.noimages|gutenberg|application/epub+zip|{"download": true}',
        ]

        mockAddPart = mocker.patch.object(GutenbergProcess, 'addNewPart')

        testInstance.storeEpubsInS3(mockRecord)

        testInstance.rabbitmq_manager.sendMessageToQueue.assert_has_calls([
            mocker.call(
                testInstance.fileQueue,
                testInstance.fileRoute,
                get_file_message('gutenberg.org/ebook/1.epub.images', 'epubs/gutenberg/1_images.epub')
            ),
            mocker.call(
                testInstance.fileQueue,
                testInstance.fileRoute,
                get_file_message('gutenberg.org/ebook/2.epub.noimages', 'epubs/gutenberg/2_noimages.epub')
            ),
        ])

        mockAddPart.assert_has_calls([
            mocker.call([], '1', 'gutenberg', '{"download": true}', 'application/epub+zip', 'epubs/gutenberg/1_images.epub'),
            mocker.call([], '1', 'gutenberg', '{"download": false}', 'application/epub+xml', 'epubs/gutenberg/1_images/META-INF/container.xml'),
            mocker.call([], '1', 'gutenberg', '{"download": false}', 'application/webpub+json', 'epubs/gutenberg/1_images/manifest.json'),
            mocker.call([], '2', 'gutenberg', '{"download": true}', 'application/epub+zip', 'epubs/gutenberg/2_noimages.epub'),
        ])

    def test_addNewPart(self, testInstance):
        testParts = []

        testInstance.addNewPart(testParts, '1', 'test', '{}', 'application/test', 'epubs/test/1.epub')

        assert testParts[0] == '1|https://test_aws_bucket.s3.amazonaws.com/epubs/test/1.epub|test|application/test|{}'

    def test_addCoverAndStoreInS3(self, testInstance, testMetadataYAML, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.record.has_part = []

        testInstance.addCoverAndStoreInS3(mockRecord, testMetadataYAML)

        testInstance.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            testInstance.fileQueue,
            testInstance.fileRoute,
            get_file_message('gutenberg.org/files/1/images/cover.jpg', 'covers/gutenberg/1.jpg')
        )
        assert mockRecord.record.has_part == [
            '|https://test_aws_bucket.s3.amazonaws.com/covers/gutenberg/1.jpg|gutenberg|image/jpeg|{"cover": true}'
        ]
        