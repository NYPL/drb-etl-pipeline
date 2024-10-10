from datetime import datetime
import pytest
import requests

from tests.helper import TestHelpers
from processes import NYPLProcess
from sqlalchemy import text


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
                self.bib_db_connection = mocker.MagicMock()
                self.nypl_api_manager = mocker.MagicMock()
                self.location_codes = {}
                self.cce_api = 'test_cce_url'
                self.ingest_offset = None
                self.ingest_limit = None
        
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
        mockImport = mocker.patch.object(NYPLProcess, 'import_bib_records')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockImport = mocker.patch.object(NYPLProcess, 'import_bib_records')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockImport.assert_called_once_with(full_or_partial=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockImport = mocker.patch.object(NYPLProcess, 'import_bib_records')
        mockSave = mocker.patch.object(NYPLProcess, 'saveRecords')
        mockCommit = mocker.patch.object(NYPLProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'customTimestamp'
        testInstance.runProcess()

        mockImport.assert_called_once_with(start_timestamp='customTimestamp')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_load_location_codes(self, testInstance, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.json.return_value = 'testLocationCodes'
        mockGet.return_value = mockResp

        testResponse = testInstance.load_location_codes()

        assert testResponse == 'testLocationCodes'
        mockGet.assert_called_once_with('test_location_url')
        mockResp.json.assert_called_once

    def test_is_pd_research_bib_post_1964(self, testInstance, testBib, mocker):
        assert testInstance.is_pd_research_bib(testBib) is False

    def test_is_pd_research_bib_no_year(self, testInstance, testBib, mocker):
        testBib['publish_year'] = None
        assert testInstance.is_pd_research_bib(testBib) is False

    def test_is_pd_research_bib_1925_to_1964_pd_non_research(self, testInstance, testBib, mocker):
        testInstance.nypl_api_manager.queryApi.return_value = {'isResearch': False}

        testBib['publish_year'] = '1950'

        mockGetCopyright = mocker.patch.object(NYPLProcess, 'get_copyright_status')
        mockGetCopyright.return_value = True
        assert testInstance.is_pd_research_bib(testBib) is False

    def test_is_pd_research_bib_pre_1925_research(self, testInstance, testBib, mocker):
        testInstance.nypl_api_manager.queryApi.return_value = {'isResearch': True}
        mockGetCopyright = mocker.patch.object(NYPLProcess, 'get_copyright_status')

        testBib['publish_year'] = '1900'

        assert testInstance.is_pd_research_bib(testBib) is True 
        mockGetCopyright.assert_not_called

    def test_get_copyright_status_no_lccn(self, testInstance, testVarFields):
        del testVarFields[1]
        assert testInstance.get_copyright_status(testVarFields) is False

    def test_get_copyright_status_api_error(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 500
        mockReq.return_value = mockResp

        assert testInstance.get_copyright_status(testVarFields) is False

    def test_get_copyright_status_no_registrations(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': []}}
        mockReq.return_value = mockResp

        assert testInstance.get_copyright_status(testVarFields) is False
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

    def test_get_copyright_status_has_renewals(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': [{'renewals': ['ren1']}]}}
        mockReq.return_value = mockResp

        assert testInstance.get_copyright_status(testVarFields) is False
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

    def test_get_copyright_status_not_renewed(self, testInstance, testVarFields, mocker):
        mockReq = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.json.return_value = {'data': {'results': [{'renewals': []}]}}
        mockReq.return_value = mockResp

        assert testInstance.get_copyright_status(testVarFields) is True
        mockReq.assert_called_once_with('test_cce_url/lccn/123456789')

    def test_fetch_bib_items_success(self, testInstance, mocker):
        testInstance.nypl_api_manager.queryApi = mocker.MagicMock()
        testInstance.nypl_api_manager.queryApi.return_value = {'data': ['item1', 'item2', 'item3']}

        testItems = testInstance.fetch_bib_items({'nypl_source': 'sierra-test', 'id': 1})

        assert testItems == ['item1', 'item2', 'item3']

    def test_fetch_bib_items_none(self, testInstance, mocker):
        testInstance.nypl_api_manager.queryApi = mocker.MagicMock()
        testInstance.nypl_api_manager.queryApi.return_value = {}

        testItems = testInstance.fetch_bib_items({'nypl_source': 'sierra-test', 'id': 1})

        assert testItems == []

    def test_parse_nypl_bib_research(self, testInstance, mocker):
        processorMocks = mocker.patch.multiple(
            NYPLProcess,
            is_pd_research_bib=mocker.DEFAULT,
            fetch_bib_items=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['is_pd_research_bib'].return_value = True
        processorMocks['fetch_bib_items'].return_value = 'testBibItems'

        mockRecord = mocker.MagicMock()
        mockMapping.return_value = mockRecord

        testInstance.parse_nypl_bib({'id': 1})

        processorMocks['is_pd_research_bib'].assert_called_once_with({'id': 1})
        processorMocks['fetch_bib_items'].assert_called_once_with({'id': 1})
        mockMapping.assert_called_once_with(
            {'id': 1}, 'testBibItems', {}, {}
        )
        mockRecord.applyMapping.assert_called_once
        processorMocks['addDCDWToUpdateList'].assert_called_once_with(mockRecord)


    def test_parse_nypl_bib_not_research(self, testInstance, mocker):
        processorMocks = mocker.patch.multiple(
            NYPLProcess,
            is_pd_research_bib=mocker.DEFAULT,
            fetch_bib_items=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )
        mockMapping = mocker.patch('processes.nypl.NYPLMapping')

        processorMocks['is_pd_research_bib'].return_value = False

        testInstance.parse_nypl_bib({'id': 1})

        processorMocks['is_pd_research_bib'].assert_called_once_with({'id': 1})
        processorMocks['fetch_bib_items'].assert_not_called
        processorMocks['addDCDWToUpdateList'].assert_not_called
        mockMapping.assert_not_called

    def test_import_bib_records_not_full_no_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.now.return_value.replace.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parse_nypl_bib')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execution_options().execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bib_db_connection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.import_bib_records()

        mockDatetime.now.assert_called_once
        mockConn.execution_options().execute.assert_called_once()
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_import_bib_records_not_full_custom_timestamp(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')
        mockDatetime.now.return_value.replace.return_value = datetime(1900, 1, 2, 12, 0, 0)

        mockParse = mocker.patch.object(NYPLProcess, 'parse_nypl_bib')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execution_options().execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bib_db_connection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.import_bib_records(start_timestamp='customTimestamp')

        mockDatetime.now.assert_not_called
        mockConn.execution_options().execute.assert_called_once()
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_import_bib_records_full(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')

        mockParse = mocker.patch.object(NYPLProcess, 'parse_nypl_bib')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execution_options().execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': None},
            {'var_fields': 'bib3'}
        ]

        testInstance.bib_db_connection.engine.connect.return_value.__enter__.return_value = mockConn

        testInstance.import_bib_records(full_or_partial=True)

        mockDatetime.now.assert_not_called
        mockConn.execution_options().execute.assert_called_once()
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib3'})])

    def test_import_bib_records_full_batch(self, testInstance, mocker):
        mockDatetime = mocker.patch('processes.nypl.datetime')

        mockParse = mocker.patch.object(NYPLProcess, 'parse_nypl_bib')

        mockConn = mocker.MagicMock(name='Mock Connection')
        mockConn.execution_options().execute.return_value = [
            {'var_fields': 'bib1'},
            {'var_fields': 'bib2'},
            {'var_fields': None}
        ]

        testInstance.ingest_offset = '1000'
        testInstance.ingest_limit = '1000'
        testInstance.bib_db_connection.engine.connect.return_value.__enter__.return_value = mockConn
        testInstance.import_bib_records(full_or_partial=True)

        mockDatetime.now.assert_not_called
        mockConn.execution_options().execute.assert_called_once()
        mockParse.assert_has_calls([mocker.call({'var_fields': 'bib1'}), mocker.call({'var_fields': 'bib2'})])
