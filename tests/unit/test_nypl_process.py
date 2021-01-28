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
                self.cceAPI = 'test_cce_url'
                self.ingestOffset = None
                self.ingestLimit = None
        
        return TestNYPLProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testBib(self):
        return {
            'id': 1,
            'nypl_source': 'test-nypl',
            'publish_year': 2020,
            'var_fields': []
        }

    @pytest.fixture
    def testVarFields(self):
        return [
            {
                'marcTag': '245'
            },
            {
                'marcTag': '010',
                'subfields': [
                    {
                        'tag': 'a',
                        'content': '123456789'
                    }
                ]
            }
        ]
    
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

    def test_isPDResearchBib_post_1964(self, testInstance, testBib, mocker):
        assert testInstance.isPDResearchBib(testBib) is False

    def test_isPDResearchBib_no_year(self, testInstance, testBib, mocker):
        testBib['publish_year'] = None
        assert testInstance.isPDResearchBib(testBib) is False

    def test_isPDResearchBib_1925_to_1964_pd_non_research(self, testInstance, testBib, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {'isResearch': False}

        testBib['publish_year'] = '1950'

        mockGetCopyright = mocker.patch.object(NYPLProcess, 'getCopyrightStatus')
        mockGetCopyright.return_value = True
        assert testInstance.isPDResearchBib(testBib) is False

    def test_isPDResearchBib_pre_1925_research(self, testInstance, testBib, mocker):
        testInstance.queryApi = mocker.MagicMock()
        testInstance.queryApi.return_value = {'isResearch': True}
        mockGetCopyright = mocker.patch.object(NYPLProcess, 'getCopyrightStatus')

        testBib['publish_year'] = '1900'

        assert testInstance.isPDResearchBib(testBib) is True 
        mockGetCopyright.assert_not_called

    def test_getCopyrightStatus_no_lccn(self, testInstance, testVarFields):
        del testVarFields[1]
        assert testInstance.getCopyrightStatus(testVarFields) is False

    def test_getCopyrightStatus_api_error(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockReq.return_value = mockResp

        assert testInstance.getCopyrightStatus(testVarFields) is False

    def test_getCopyrightStatus_no_registrations(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': []}}
        mockReq.return_value = mockResp

        assert testInstance.getCopyrightStatus(testVarFields) is False
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

    def test_getCopyrightStatus_has_renewals(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': [{'renewals': ['ren1']}]}}
        mockReq.return_value = mockResp

        assert testInstance.getCopyrightStatus(testVarFields) is False
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

    def test_getCopyrightStatus_not_renewed(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': [{'renewals': []}]}}
        mockReq.return_value = mockResp

        assert testInstance.getCopyrightStatus(testVarFields) is True
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

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
            isPDResearchBib=mocker.DEFAULT,
            fetchBibItems=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['isPDResearchBib'].return_value = True
        processorMocks['fetchBibItems'].return_value = 'testBibItems'

        mockRecord = mocker.MagicMock()
        mockMapping.return_value = mockRecord

        testInstance.parseNYPLDataRow({'id': 1})

        processorMocks['isPDResearchBib'].assert_called_once_with({'id': 1})
        processorMocks['fetchBibItems'].assert_called_once_with({'id': 1})
        mockMapping.assert_called_once_with(
            {'id': 1}, 'testBibItems', {}, {}
        )
        mockRecord.applyMapping.assert_called_once
        processorMocks['addDCDWToUpdateList'].assert_called_once_with(mockRecord)


    def test_parseNYPLDataRow_not_research(self, testInstance, mocker):
        processorMocks = mocker.patch.multiple(
            NYPLProcess,
            isPDResearchBib=mocker.DEFAULT,
            fetchBibItems=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['isPDResearchBib'].return_value = False

        testInstance.parseNYPLDataRow({'id': 1})

        processorMocks['isPDResearchBib'].assert_called_once_with({'id': 1})
        processorMocks['fetchBibItems'].assert_not_called
        processorMocks['addDCDWToUpdateList'].assert_not_called
        mockMapping.assert_not_called

    def test_importBibRecords_not_full_no_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords()

        mockDatetime.utcnow.assert_called_once
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib WHERE updated_date > \'1900-01-01T12:00:00\''
        )
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_importBibRecords_not_full_custom_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.utcnow.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords(startTimestamp='customTimestamp')

        mockDatetime.utcnow.assert_not_called
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib WHERE updated_date > \'customTimestamp\''
        )
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_importBibRecords_full(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.importBibRecords(fullOrPartial=True)

        mockDatetime.utcnow.assert_not_called
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib'
        )
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_importBibRecords_full_batch(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')

        mockParse = mocker.patch.object(NYPLProcess, 'parseNYPLDataRow')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': 'bib2'},
            {'var_fields': None}
        ]

        testInstance.ingestOffset = '1000'
        testInstance.ingestLimit = '1000'
        testInstance.bibDBConnection.engine.connect.return_value.__enter__.return_value = mockConn
        testInstance.importBibRecords(fullOrPartial=True)

        mockDatetime.utcnow.assert_not_called
        mockConn.execute.assert_called_once_with(
            'SELECT * FROM bib OFFSET 1000 LIMIT 1000'
        )
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib2'})])
