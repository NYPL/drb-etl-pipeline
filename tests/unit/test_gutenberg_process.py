from datetime import datetime
import os
import pytest

from tests.helper import TestHelpers
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
                self.statics = {}
                self.ingestOffset = 0
                self.ingestLimit = 5000
                self.s3Bucket = os.environ['FILE_BUCKET']
                self.fileQueue = os.environ['FILE_QUEUE']
                self.fileRoute = os.environ['FILE_ROUTING_KEY']
        
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
        mockSave = mocker.patch.object(GutenbergProcess, 'saveRecords')
        mockCommit = mocker.patch.object(GutenbergProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(GutenbergProcess, 'importRDFRecords')
        mockSave = mocker.patch.object(GutenbergProcess, 'saveRecords')
        mockCommit = mocker.patch.object(GutenbergProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once_with(fullImport=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockImport = mocker.patch.object(GutenbergProcess, 'importRDFRecords')
        mockSave = mocker.patch.object(GutenbergProcess, 'saveRecords')
        mockCommit = mocker.patch.object(GutenbergProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testPeriod'
        testInstance.runProcess()

        mockImport.assert_called_once_with(startTimestamp='testPeriod')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_importRDFRecords_partial(self, testInstance, mocker):
        mockProcess = mocker.patch.object(GutenbergProcess, 'processGutenbergBatch')
        mockManager = mocker.MagicMock()
        mockManager.fetchGithubRepoBatch.side_effect = [True, False]
        mockManager.dataFiles = 'testDataFiles'
        mockManagerInit = mocker.patch('processes.gutenberg.GutenbergManager')
        mockManagerInit.return_value = mockManager

        mockDateTime = mocker.patch('processes.gutenberg.datetime')
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
        mockManagerInit = mocker.patch('processes.gutenberg.GutenbergManager')
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
        mockManagerInit = mocker.patch('processes.gutenberg.GutenbergManager')
        mockManagerInit.return_value = mockManager

        testInstance.importRDFRecords(fullImport=True)

        mockManagerInit.assert_called_once_with('ASC', 'CREATED_AT', None, 100)
        mockProcess.assert_has_calls([mocker.call('testDataFiles'), mocker.call('testDataFiles')])
        assert mockManager.fetchGithubRepoBatch.call_count == 2
        assert mockManager.fetchMetadataFilesForBatch.call_count == 2
        assert mockManager.resetBatch.call_count == 2

    def test_processGutenbergBatch(self, testInstance, mocker):
        mockGutenbergRec = mocker.MagicMock(name='MockRecord', record=mocker.MagicMock(source_id=1))
        mockGutenbergInit = mocker.patch('processes.gutenberg.GutenbergMapping')
        mockGutenbergInit.return_value = mockGutenbergRec

        processMocks = mocker.patch.multiple(
            GutenbergProcess,
            storeEpubsInS3=mocker.DEFAULT,
            addCoverAndStoreInS3=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
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
        processMocks['addDCDWToUpdateList'].assert_has_calls([
            mocker.call(mockGutenbergRec), mocker.call(mockGutenbergRec)
        ])

    def test_storeEpubsInS3(self, testInstance, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.record.has_part = [
            '1|gutenberg.org/ebook/1.epub.images|gutenberg|application/epub+zip|{"download": true}',
            '1|gutenberg.org/ebook/1.epub.images|gutenberg|application/epub|{"download": false}',
            '2|gutenberg.org/ebook/2.epub.noimages|gutenberg|application/epub+zip|{"download": true}',
        ]

        mockSendToQueue = mocker.patch.object(GutenbergProcess, 'sendFileToProcessingQueue')
        mockAddPart = mocker.patch.object(GutenbergProcess, 'addNewPart')

        testInstance.storeEpubsInS3(mockRecord)

        mockSendToQueue.assert_has_calls([
            mocker.call('gutenberg.org/ebook/1.epub.images', 'epubs/gutenberg/1_images.epub'),
            mocker.call('gutenberg.org/ebook/2.epub.noimages', 'epubs/gutenberg/2_noimages.epub')
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

        mockSendToQueue = mocker.patch.object(GutenbergProcess, 'sendFileToProcessingQueue')

        testInstance.addCoverAndStoreInS3(mockRecord, testMetadataYAML)

        mockSendToQueue.assert_called_once_with(
            'gutenberg.org/files/1/images/cover.jpg', 'covers/gutenberg/1.jpg'
        )
        assert mockRecord.record.has_part == [
            '|https://test_aws_bucket.s3.amazonaws.com/covers/gutenberg/1.jpg|gutenberg|image/jpeg|{"cover": true}'
        ]
    
    def test_sendFileToProcessingQueue(self, testInstance, mocker):
        mockMessageSend = mocker.patch.object(GutenbergProcess, 'sendMessageToQueue')

        testInstance.sendFileToProcessingQueue('testURL', 'testLocation')

        mockMessageSend.assert_called_once_with(
            'test_file_queue', 
            'test_file_key',
            {'fileData': {'fileURL': 'testURL', 'bucketPath': 'testLocation'}}
        )
        