import csv
import gzip
import pytest
import requests

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
        
        return TestHathiProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def hathiFilesData(self):
        return [
            {'created': '2020-01-01T00:00:00-0', 'url': 'hathiUrl1', 'full': False},
            {'created': '2019-01-01T00:00:00-0', 'url': 'hathiUrl2', 'full': True},
            {'created': '2018-01-01T00:00:00-0', 'url': 'hathiUrl3', 'full': False}
        ]

    @pytest.fixture
    def hathiTSV(self):
        rows = []
        for i in range(1000):
            rightsStmt = 'ic' if i % 3 == 0 else 'pd'
            rows.append([i, 'hathi', rightsStmt])

        return rows

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

    def test_importFromSpecificFile_success(self, testInstance, mocker, hathiTSV):
        mockOpen = mocker.patch('processes.hathiTrust.open')
        mockOpen.return_value = 'csvFile'

        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = hathiTSV

        mockParser = mocker.patch.object(HathiTrustProcess, 'parseHathiDataRow')

        testInstance.importFromSpecificFile('testFile')

        mockOpen.assert_called_once_with('testFile', newline='')
        mockCSVReader.assert_called_once_with('csvFile')

        assert mockParser.call_count == 666

    def test_importFromSpecificFile_error(self, testInstance, mocker):
        mockOpen = mocker.patch('processes.hathiTrust.open')
        mockOpen.side_effect = FileNotFoundError

        with pytest.raises(IOError):
            testInstance.importFromSpecificFile('testFile')

    def test_parseHathiDataRow(self, testInstance, mocker):
        mockHathiMapping = mocker.patch('processes.hathiTrust.HathiMapping')
        mockAddDCDW = mocker.patch.object(HathiTrustProcess, 'addDCDWToUpdateList')

        testInstance.parseHathiDataRow('testRow')

        mockHathiMapping.assert_called_once_with('testRow', {})
        mockHathiMapping.applyMapping.assert_called_once
        mockAddDCDW.assert_called_once

    def test_importFromHathiTrustDataFile_standard(self, testInstance, hathiFilesData, hathiTSV, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockListResponse = mocker.MagicMock()
        mockTSVResponse = mocker.MagicMock()
        mockRequest.side_effect = [mockListResponse, mockTSVResponse]
        mockListResponse.status_code = 200
        mockListResponse.json.return_value = hathiFilesData

        mockOpen = mocker.patch('processes.hathiTrust.open')
        mockTSV = mocker.MagicMock()
        mockOpen.return_value.__enter__.return_value = mockTSV

        mockGzip = mocker.patch.object(gzip, 'open')
        mockCSVReader = mocker.patch.object(csv, 'reader')
        mockCSVReader.return_value = hathiTSV

        mockHathiMapping = mocker.patch('processes.hathiTrust.HathiMapping')
        mockAddDCDW = mocker.patch.object(HathiTrustProcess, 'addDCDWToUpdateList')

        testInstance.importFromHathiTrustDataFile()

        mockRequest.assert_has_calls([
            mocker.call('test_hathi_url'), mocker.call('hathiUrl1')
        ])
        mockTSV.write.assert_called_once
        mockCSVReader.assert_called_once
        assert mockHathiMapping.call_count == 666
        assert mockAddDCDW.call_count == 666

    def test_importFromHathiTrustDataFile_error(self, testInstance, mocker):
        mockRequest = mocker.patch.object(requests, 'get')
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 500

        with pytest.raises(IOError):
            testInstance.importFromHathiTrustDataFile()
            mockRequest.assert_called_once
