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
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock(db_manager=self.db_manager)
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
            'close': mocker.patch.object(NYPLProcess, 'close_connection'),
            'add_record': mocker.patch.object(NYPLProcess, 'addDCDWToUpdateList')
        }
    
    @pytest.fixture
    def record_mappings(self, mocker):
        return [mocker.MagicMock()]
    
    def test_runProcess_daily(self, test_instance: NYPLProcess, record_mappings):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings

        test_instance.process = 'daily'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(offset=None, limit=None)
        assert test_instance.record_buffer.flush.call_count == len(record_mappings)
        test_instance.record_buffer.flush.assert_called_once
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_complete(self, test_instance: NYPLProcess, record_mappings):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings

        test_instance.process = 'complete'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(full_import=True)
        assert test_instance.record_buffer.flush.call_count == len(record_mappings)
        test_instance.record_buffer.flush.assert_called_once
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_custom(self, test_instance: NYPLProcess, record_mappings):
        test_instance.nypl_bib_service.get_records.return_value = record_mappings
        
        test_instance.process = 'custom'
        test_instance.runProcess()

        test_instance.nypl_bib_service.get_records.assert_called_once_with(start_timestamp=None, offset=None, limit=None)
        assert test_instance.record_buffer.add.call_count == len(record_mappings)
        test_instance.record_buffer.flush.assert_called_once
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_unknown(self, test_instance: NYPLProcess):
        test_instance.process = 'unknown'
        test_instance.runProcess()
        
        test_instance.nypl_bib_service.get_records.assert_not_called()
        test_instance.record_buffer.add.assert_not_called()
        test_instance.record_buffer.flush.assert_not_called()
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_error(self, test_instance: NYPLProcess, mocks):
        test_instance.nypl_bib_service.get_records.side_effect = Exception()

        test_instance.process = 'daily'

        with pytest.raises(Exception):
            test_instance.runProcess()

        test_instance.record_buffer.add.assert_not_called()
        test_instance.record_buffer.flush.assert_not_called()
        test_instance.db_manager.close_connection.assert_called_once()
