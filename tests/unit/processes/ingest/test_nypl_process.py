import pytest

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
    def test_instance(self, mocker) -> NYPLProcess:
        class TestNYPLProcess(NYPLProcess):
            def __init__(self, *args):
                self.nypl_bib_service = mocker.MagicMock()
                self.offset = None
                self.limit = None
                self.ingestPeriod = None
                self.records = []
        
        return TestNYPLProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def mocks(self, mocker):
        return {
            'generate_engine': mocker.patch.object(NYPLProcess, 'generateEngine'),
            'create_session': mocker.patch.object(NYPLProcess, 'createSession'),
            'save': mocker.patch.object(NYPLProcess, 'saveRecords'),
            'commit': mocker.patch.object(NYPLProcess, 'commitChanges'),
            'close': mocker.patch.object(NYPLProcess, 'close_connection'),
            'add_record': mocker.patch.object(NYPLProcess, 'addDCDWToUpdateList')
        }
    
    @pytest.fixture
    def record_mappings(self, mocker):
        return [mocker.MagicMock()]
    
    def assert_common_expectations(self, mocks):
        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['save'].assert_called_once()
        mocks['commit'].assert_called_once()
        mocks['close'].assert_called_once()
    
    def test_runProcess_daily(self, test_instance: NYPLProcess, record_mappings, mocks):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings

        test_instance.process = 'daily'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(offset=None, limit=None)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_complete(self, test_instance: NYPLProcess, record_mappings, mocks):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings

        test_instance.process = 'complete'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(full_import=True)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_custom(self, test_instance: NYPLProcess, record_mappings, mocks):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings
        
        test_instance.process = 'custom'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(start_timestamp=None, offset=None, limit=None)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_unknown(self, test_instance: NYPLProcess, mocks):
        test_instance.process = 'unknown'
        test_instance.runProcess()
        
        test_instance.nypl_bib_service.get_records.assert_not_called()

        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['commit'].assert_not_called()
        mocks['save'].assert_not_called()
        mocks['add_record'].assert_not_called()
        mocks['close'].assert_called_once()

    def test_runProcess_error(self, test_instance: NYPLProcess, mocks):
        test_instance.nypl_bib_service.get_records.side_effect = Exception()

        test_instance.process = 'daily'

        with pytest.raises(Exception):
            test_instance.runProcess()

        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['commit'].assert_not_called()
        mocks['save'].assert_not_called()
        mocks['add_record'].assert_not_called()
        mocks['close'].assert_called_once()
