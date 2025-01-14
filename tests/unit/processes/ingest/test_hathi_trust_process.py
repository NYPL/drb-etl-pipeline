import csv
import gzip
import pytest
import requests
from requests.exceptions import HTTPError
from datetime import datetime, timedelta, timezone

from tests.helper import TestHelpers
from processes import HathiTrustProcess


class TestHathiTrustProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestHathiProcess(HathiTrustProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.constants = {}
                self.records = []
                self.ingest_limit = None
        
        return TestHathiProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def hathiFilesData(self):
        return [
            {'created': '2020-01-01T00:00:00-0000', 'url': 'hathiUrl1', 'full': False, 'modified': '2024-10-28 11:00:00 Z'},
            {'created': '2019-01-01T00:00:00-0000', 'url': 'hathiUrl2', 'full': True, 'modified': '2024-10-28 11:00:00 Z'},
            {'created': '2018-01-01T00:00:00-0000', 'url': 'hathiUrl3', 'full': False, 'modified': '2024-10-28 12:00:00 Z'}
        ]

    @pytest.fixture
    def hathiTSV(self):
        def tsvIter():
            for i in range(200):
                rightsStmt = 'ic' if i % 3 == 0 else 'pd'
                yield [i, 'hathi', rightsStmt]
        
        return tsvIter()
    
    @pytest.fixture
    def hathiTSV2(self):
        def tsvIter():
            for i in range(200):
                rightsStmt = 'ic' if i % 3 == 0 else 'pd'
                yield [i, 'hathi', rightsStmt, '', '', '', '', '', '', '', '', '', '', '', '2024-10-28 12:00:00']
        
        return tsvIter()
    
    @pytest.fixture
    def start_date_time(self):
        return datetime.strptime('2024-10-27 19:37:21.385454', '%Y-%m-%d %H:%M:%S.%f').replace(tzinfo=None)

    def test_runProcess_daily(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiTrustDataFile')
        mockSave = mocker.patch.object(HathiTrustProcess, 'saveRecords')
        mockCommit = mocker.patch.object(HathiTrustProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiTrustDataFile')
        mockSave = mocker.patch.object(HathiTrustProcess, 'saveRecords')
        mockCommit = mocker.patch.object(HathiTrustProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromSpecificFile')
        mockSave = mocker.patch.object(HathiTrustProcess, 'saveRecords')
        mockCommit = mocker.patch.object(HathiTrustProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.customFile = 'testFile'
        testInstance.runProcess()

        mockImport.assert_called_once_with('testFile')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_importFromSpecificFile_success(self, testInstance, mocker):
        mockOpen = mocker.patch('processes.ingest.hathi_trust.open')
        mockOpen.return_value = 'csvFile'

        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = 'testCSV'

        mockReader = mocker.patch.object(HathiTrustProcess, 'readHathiFile')

        testInstance.importFromSpecificFile('testFile')

        mockOpen.assert_called_once_with('testFile', new_line='')
        mockCSVReader.assert_called_once_with('csvFile', delimiter='\t')
        mockReader.assert_called_once_with('testCSV')

    def test_importFromSpecificFile_error(self, testInstance, mocker):
        mockOpen = mocker.patch('processes.ingest.hathi_trust.open')
        mockOpen.side_effect = FileNotFoundError

        with pytest.raises(IOError):
            testInstance.importFromSpecificFile('testFile')

    def test_parseHathiDataRow(self, testInstance, mocker):
        mockHathiMapping = mocker.patch('processes.ingest.hathi_trust.HathiMapping')
        mockAddDCDW = mocker.patch.object(HathiTrustProcess, 'addDCDWToUpdateList')

        testInstance.parseHathiDataRow('testRow')

        mockHathiMapping.assert_called_once_with('testRow', {})
        mockHathiMapping.applyMapping.assert_called_once
        mockAddDCDW.assert_called_once

    def test_importFromHathiTrustDataFile_standard(self, testInstance, hathiFilesData, start_date_time, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockListResponse = mocker.MagicMock()
        mockRequest.return_value = mockListResponse
        mockListResponse.json.return_value = hathiFilesData

        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiFile')

        testInstance.importFromHathiTrustDataFile(start_date_time=start_date_time)

        mockRequest.assert_called_once_with(HathiTrustProcess.HATHI_DATAFILES, timeout=15)
        mockImport.assert_called_with('hathiUrl3', start_date_time)
        
    def test_importFromHathiTrustDataFile_error(self, testInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.raise_for_status.side_effect = HTTPError
        mockRequest.return_value = mockResponse

        with pytest.raises(IOError):
            testInstance.importFromHathiTrustDataFile()
            mockRequest.assert_called_once

    def test_importFromHathiFile_success(self, testInstance, start_date_time, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock(content=b'testContent')
        mockGet.return_value = mockResp

        mockOpen = mocker.patch.object(gzip, 'open')
        mockOpen.return_value.__enter__.return_value = 'testGzip'

        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = 'testCSV'

        mockReadFile = mocker.patch.object(HathiTrustProcess, 'readHathiFile')

        testInstance.importFromHathiFile('testURL', start_date_time)

        mockGet.assert_called_once_with('testURL', stream=True, timeout=30)
        mockOpen.assert_called_once() # Cannot compare BytesIO objects
        mockCSVReader.assert_called_once_with('testGzip', delimiter='\t')
        mockReadFile.assert_called_once_with('testCSV', start_date_time)

    def test_importFromHathiFile_error(self, testInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.raise_for_status.side_effect = HTTPError
        mockRequest.return_value = mockResponse

        assert testInstance.importFromHathiFile('badURL') == None

    def test_readHathiFile(self, testInstance, hathiTSV2, start_date_time, mocker):
        mockParseRow = mocker.patch.object(HathiTrustProcess, 'parseHathiDataRow')

        testInstance.readHathiFile(hathiTSV2, start_date_time)

        assert mockParseRow.call_count == 133
