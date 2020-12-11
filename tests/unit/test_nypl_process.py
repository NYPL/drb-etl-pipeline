from datetime import datetime
import pytest
import requests

from tests.helper import TestHelpers
from processes import NYPLProcess


class TestNYPLProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestNYPLProcess(NYPLProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.statics = {}
                self.bibDBConnection = mocker.MagicMock()
                self.locationCodes = {}
        
        return TestNYPLProcess('TestProcess', 'testFile', 'testDate')
    
    def test_runProcess_daily(self, testInstance, mocker):
        mockImport = mocker.patch.object(NYPLProcess, 'importBibRecords')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(NYPLProcess, 'importBibRecords')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once_with(fullOrPartial=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockImport = mocker.patch.object(NYPLProcess, 'importBibRecords')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'customTimestamp'
        testInstance.runProcess()

        mockImport.assert_called_once_with(startTimestamp='customTimestamp')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_loadLocationCodes(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.json.return_value = 'testLocationCodes'
        mockGet.return_value = mockResp

        testResponse = testInstance.loadLocationCodes()

        assert testResponse == 'testLocationCodes'
        mockGet.assert_called_once_with('test_location_url')
        mockResp.json.assert_called_once

    def test_isResearchBib_true(self, testInstance, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {'isResearch': True}

        assert testInstance.isResearchBib({'nypl_source': 'sierra-test', 'id': 1}) is True

    def test_isResearchBib_false(self, testInstance, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {'isResearch': False}

        assert testInstance.isResearchBib({'nypl_source': 'sierra-test', 'id': 1}) is False

    def test_fetchBibItems_success(self, testInstance, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {'data': ['item1', 'item2', 'item3']}

        testItems = testInstance.fetchBibItems({'nypl_source': 'sierra-test', 'id': 1})

        assert testItems == ['item1', 'item2', 'item3']

    def test_fetchBibItems_none(self, testInstance, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {}

        testItems = testInstance.fetchBibItems({'nypl_source': 'sierra-test', 'id': 1})

        assert testItems == []

    def test_parseNYPLDataRow_research(self, testInstance, mocker):
        processorMocks = mocker.patch.multiple(
            NYPLProcess,
            isResearchBib=mocker.DEFAULT,
            fetchBibItems=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['isResearchBib'].return_value = True
        processorMocks['fetchBibItems'].return_value = 'testBibItems'

        mockRecord = mocker.MagicMock()
        mockMapping.return_value = mockRecord

        testInstance.parseNYPLDataRow({'id': 1})

        processorMocks['isResearchBib'].assert_called_once_with({'id': 1})
        processorMocks['fetchBibItems'].assert_called_once_with({'id': 1})
        mockMapping.assert_called_once_with(
            {'id': 1}, 'testBibItems', {}, {}
        )
        mockRecord.applyMapping.assert_called_once
        processorMocks['addDCDWToUpdateList'].assert_called_once_with(mockRecord)


    def test_parseNYPLDataRow_not_research(self, testInstance, mocker):
        processorMocks = mocker.patch.multiple(
            NYPLProcess,
            isResearchBib=mocker.DEFAULT,
            fetchBibItems=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['isResearchBib'].return_value = False

        testInstance.parseNYPLDataRow({'id': 1})

        processorMocks['isResearchBib'].assert_called_once_with({'id': 1})
        processorMocks['fetchBibItems'].assert_not_called
        processorMocks['addDCDWToUpdateList'].assert_not_called
        mockMapping.assert_not_called

    def test_importBibRecords_not_full_no_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = ['bib1', 'bib2', 'bib3']

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords()

        mockDatetime.utcnow.assert_called_once
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib WHERE updated_date > \'1900-01-01T12:00:00-000000\''
        )
        mockParse.assert_has_calls([mocker.call('bib1'), mocker.call('bib2'), mocker.call('bib3')])

    def test_importBibRecords_not_full_custom_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = ['bib1', 'bib2', 'bib3']

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords(startTimestamp='customTimestamp')

        mockDatetime.utcnow.assert_not_called
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib WHERE updated_date > \'customTimestamp\''
        )
        mockParse.assert_has_calls([mocker.call('bib1'), mocker.call('bib2'), mocker.call('bib3')])

    def test_importBibRecords_full(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = ['bib1', 'bib2', 'bib3']

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords(fullOrPartial=True)

        mockDatetime.utcnow.assert_not_called
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib'
        )
        mockParse.assert_has_calls([mocker.call('bib1'), mocker.call('bib2'), mocker.call('bib3')])
