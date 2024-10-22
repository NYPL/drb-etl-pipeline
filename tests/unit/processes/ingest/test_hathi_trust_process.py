import csv
import gzip
import pytest
import requests
from requests.exceptions import HTTPError

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
                self.statics = {}
                self.records = []
                self.ingest_limit = None
        
        return TestHathiProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def hathiFilesData(self):
        return [
            {'created': '2020-01-01T00:00:00-0000', 'url': 'hathiUrl1', 'full': False},
            {'created': '2019-01-01T00:00:00-0000', 'url': 'hathiUrl2', 'full': True},
            {'created': '2018-01-01T00:00:00-0000', 'url': 'hathiUrl3', 'full': False}
        ]

    @pytest.fixture
    def hathiTSV(self):
        def tsvIter():
            for i in range(1000):
                rightsStmt = 'ic' if i % 3 == 0 else 'pd'
                yield [i, 'hathi', rightsStmt]
            
            raise csv.Error
        
        return tsvIter()

    def test_runProcess_daily(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importRemoteRecords')
        mockSave = mocker.patch.object(HathiTrustProcess, 'saveRecords')
        mockCommit = mocker.patch.object(HathiTrustProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importRemoteRecords')
        mockSave = mocker.patch.object(HathiTrustProcess, 'saveRecords')
        mockCommit = mocker.patch.object(HathiTrustProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once_with(fullOrPartial=True)
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

    def test_importRemoteRecords_partial(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiTrustDataFile')
        
        testInstance.importRemoteRecords()
        
        mockImport.assert_called_once_with(fullDump=False)

    def test_importRemoteRecords_full(self, testInstance, mocker):
        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiTrustDataFile')
        
        testInstance.importRemoteRecords(fullOrPartial=True)
        
        mockImport.assert_called_once_with(fullDump=True)

    def test_importFromSpecificFile_success(self, testInstance, mocker):
        mockOpen = mocker.patch('processes.ingest.hathi_trust.open')
        mockOpen.return_value = 'csvFile'

        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = 'testCSV'

        mockReader = mocker.patch.object(HathiTrustProcess, 'readHathiFile')

        testInstance.importFromSpecificFile('testFile')

        mockOpen.assert_called_once_with('testFile', newline='')
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

    def test_importFromHathiTrustDataFile_standard(self, testInstance, hathiFilesData, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockListResponse = mocker.MagicMock()
        mockRequest.return_value = mockListResponse
        mockListResponse.json.return_value = hathiFilesData

        mockImport = mocker.patch.object(HathiTrustProcess, 'importFromHathiFile')

        testInstance.importFromHathiTrustDataFile()

        mockRequest.assert_called_once_with('test_hathi_url', timeout=15)
        mockImport.assert_called_once_with('hathiUrl1')

    def test_importFromHathiTrustDataFile_error(self, testInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.raise_for_status.side_effect = HTTPError
        mockRequest.return_value = mockResponse

        with pytest.raises(IOError):
            testInstance.importFromHathiTrustDataFile()
            mockRequest.assert_called_once

    def test_importFromHathiFile_success(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock(content=b'testContent')
        mockGet.return_value = mockResp

        mockOpen = mocker.patch.object(gzip, 'open')
        mockOpen.return_value.__enter__.return_value = 'testGzip'

        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = 'testCSV'

        mockReadFile = mocker.patch.object(HathiTrustProcess, 'readHathiFile')

        testInstance.importFromHathiFile('testURL')

        mockGet.assert_called_once_with('testURL', stream=True, timeout=30)
        mockOpen.assert_called_once() # Cannot compare BytesIO objects
        mockCSVReader.assert_called_once_with('testGzip', delimiter='\t')
        mockReadFile.assert_called_once_with('testCSV')

    def test_importFromHathiFile_error(self, testInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.raise_for_status.side_effect = HTTPError
        mockRequest.return_value = mockResponse

        assert testInstance.importFromHathiFile('badURL') == None

    def test_readHathiFile(self, testInstance, hathiTSV, mocker):
        mockParseRow = mocker.patch.object(HathiTrustProcess, 'parseHathiDataRow')

        testInstance.readHathiFile(hathiTSV)

        assert mockParseRow.call_count == 666
