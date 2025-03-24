import csv
from datetime import datetime
import pytest
import requests
from requests.exceptions import HTTPError

from processes.ingest.muse import MUSEProcess, MUSEError
from model import get_file_message
from tests.helper import TestHelpers


class TestMUSEProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestMUSE(MUSEProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.records = []
                self.ingest_limit = None
                self.fileQueue = 'fileQueue'
                self.fileRoute = 'fileRoute'
                self.rabbitmq_manager = mocker.MagicMock()

        return TestMUSE()

    @pytest.fixture
    def testMUSEPage(self):
        return open('./tests/fixtures/muse_book_42.html', 'r').read()

    @pytest.fixture
    def testMUSEPageUnreleased(self):
        return open('./tests/fixtures/muse_book_63320.html', 'r').read()

    @pytest.fixture
    def testBookCSV(self):
        return [
            ['Header 1'],
            ['Header 2'],
            ['Header 3'],
            ['Header 4'],
            [0, 1, 2, 3, 4, 5, 6, 'row1', 8, 9, 10, '2020-01-01'],
            [0, 1, 2, 3, 4, 5, 6, 'row2', 8, 9, 10],
            [0, 1, 2, 3, 4, 5, 6, 'row3', 8, 9, 10, '2020-01-01'],
        ]

    def test_runProcess_daily(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'daily'
        testProcess.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'complete'
        testProcess.runProcess()

        mockImport.assert_called_once_with(full=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testProcess, mocker):
        mockImport = mocker.patch.object(MUSEProcess, 'importMARCRecords')
        mockSave = mocker.patch.object(MUSEProcess, 'saveRecords')
        mockCommit = mocker.patch.object(MUSEProcess, 'commitChanges')

        testProcess.process = 'custom'
        testProcess.ingestPeriod = 'customTimestamp'
        testProcess.runProcess()

        mockImport.assert_called_once_with(startTimestamp='customTimestamp')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_importMARCRecords_daily(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(
            MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['recordToBeUpdated'].side_effect = [True, False, True, True]
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None]

        mockDatetime = mocker.patch('processes.ingest.muse.datetime')
        mockDatetime.now.return_value.replace.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockReader = mocker.patch('processes.ingest.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords()

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        testDate = datetime(1900, 1, 1, 12, 0, 0)
        processMocks['recordToBeUpdated'].assert_has_calls([
            mocker.call('rec1', testDate, None),
            mocker.call('rec2', testDate, None),
            mocker.call('rec3', testDate, None),
            mocker.call('rec4', testDate, None),
        ])
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_importMARCRecords_custom(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(
            MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['recordToBeUpdated'].side_effect = [True, False, True, True]
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None]

        mockReader = mocker.patch('processes.ingest.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords(startTimestamp='2020-01-01')

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        testDate = datetime(2020, 1, 1)
        processMocks['recordToBeUpdated'].assert_has_calls([
            mocker.call('rec1', testDate, None),
            mocker.call('rec2', testDate, None),
            mocker.call('rec3', testDate, None),
            mocker.call('rec4', testDate, None),
        ])
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_importMARCRecords_full(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(
            MUSEProcess,
            downloadRecordUpdates=mocker.DEFAULT,
            downloadMARCRecords=mocker.DEFAULT,
            recordToBeUpdated=mocker.DEFAULT,
            parseMuseRecord=mocker.DEFAULT,
        )
        processMocks['downloadMARCRecords'].return_value = 'mockFile'
        processMocks['parseMuseRecord'].side_effect = [None, MUSEError('test'), None, None]

        mockReader = mocker.patch('processes.ingest.muse.MARCReader')
        mockReader.return_value = ['rec1', 'rec2', 'rec3', 'rec4']

        testProcess.importMARCRecords(full=True)

        processMocks['downloadRecordUpdates'].assert_called_once()
        processMocks['downloadMARCRecords'].assert_called_once()
        mockReader.assert_called_once_with('mockFile')
        processMocks['recordToBeUpdated'].assert_not_called()
        processMocks['parseMuseRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec2'), mocker.call('rec3'), mocker.call('rec4')
        ])

    def test_downloadMARCRecords_success(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.iter_content.return_value = [b'm', b'a', b'r', b'c']
        mockGet.return_value = mockResp

        testRecords = testProcess.downloadMARCRecords()

        assert testRecords.read() == b'marc'
        mockGet.assert_called_once_with(MUSEProcess.MARC_URL, stream=True, timeout=30)

    def test_downloadMARCRecords_failure(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.raise_for_status.side_effect = HTTPError
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.downloadMARCRecords()

    def test_downloadRecordUpdates_success(self, testProcess, testBookCSV, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.iter_lines.return_value = 'testFile'
        mockGet.return_value = mockResp

        mockCSV = mocker.patch.object(csv, 'reader')
        mockCSV.return_value = iter(testBookCSV)

        testProcess.downloadRecordUpdates()

        assert testProcess.updateDates == {'row1': datetime(2020, 1, 1), 'row3': datetime(2020, 1, 1)}
        mockGet.assert_called_once_with(MUSEProcess.MARC_CSV_URL, stream=True, timeout=30)
        mockResp.iter_lines.assert_called_once_with(decode_unicode=True)
        mockCSV.assert_called_once_with('testFile', skipinitialspace=True)

    def test_downloadRecordUpdates_failure(self, testProcess, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.raise_for_status.side_effect = HTTPError
        mockGet.return_value = mockResp

        with pytest.raises(Exception):
            testProcess.downloadRecordUpdates()

    def test_recordToBeUpdated_true(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.get_fields.return_value = [{'u': 'https://muse.jhu.edu/book/1/'}]

        testProcess.updateDates = {'https://muse.jhu.edu/book/1': datetime(2020, 1, 1)}

        assert testProcess.recordToBeUpdated(mockRecord, datetime(1900, 1, 1), None) == True

    def test_recordToBeUpdated_false(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.get_fields.return_value = [{'u': 'https://muse.jhu.edu/book/1/'}]

        testProcess.updateDates = {'https://muse.jhu.edu/book/1': datetime(1900, 1, 1)}

        assert testProcess.recordToBeUpdated(mockRecord, datetime(2020, 1, 1), None) == False

    def test_parseMuseRecord(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.has_part = ['1|testURL|muse|type|flags']

        mockMapping = mocker.MagicMock()
        mockMapping.record = mockRecord
        mockMapper = mocker.patch('processes.ingest.muse.MUSEMapping')
        mockMapper.return_value = mockMapping

        mockToJson = mocker.MagicMock(return_value='testManifest')
        mockManager = mocker.MagicMock(
            epubURL='testURL',
            s3EpubPath='testPath',
            s3PDFReadPath='testPDFPath',
            s3Bucket='testBucket',
            pdfWebpubManifest=mocker.MagicMock(toJson=mockToJson)
        )
        mockManagerInit = mocker.patch('processes.ingest.muse.MUSEManager')
        mockManagerInit.return_value = mockManager

        processMocks = mocker.patch.multiple(MUSEProcess, addDCDWToUpdateList=mocker.DEFAULT)

        testProcess.parseMuseRecord('testMARC')

        mockMapper.assert_called_once_with('testMARC')
        mockMapping.applyMapping.assert_called_once()

        mockManager.parseMusePage.assert_called_once()
        mockManager.identifyReadableVersions.assert_called_once()
        mockManager.addReadableLinks.assert_called_once()

        testProcess.s3_manager.putObjectInBucket.assert_called_once_with(
            b'testManifest', 'testPDFPath', 'testBucket'
        )
        testProcess.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            testProcess.fileQueue, 
            testProcess.fileRoute, 
            get_file_message('testURL', 'testPath')
        )
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)
