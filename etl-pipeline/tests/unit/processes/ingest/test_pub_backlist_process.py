import pytest
from unittest.mock import ANY

from tests.helper import TestHelpers
from processes import PublisherBacklistProcess


class TestPublisherBacklistProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def test_instance(self, mocker) -> PublisherBacklistProcess:
        class TestPublisherBacklistProcess(PublisherBacklistProcess):
            def __init__(self, *args):
                self.publisher_backlist_service = mocker.MagicMock()
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock()
                self.ingest_period = None
                self.offset = None
                self.limit = None
                self.ingestPeriod = None
                self.records = []
        
        return TestPublisherBacklistProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def record_mappings(self, mocker):
        return [mocker.MagicMock()]
    
    def test_runProcess_daily(self, test_instance: PublisherBacklistProcess, record_mappings):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings

        test_instance.process = 'daily'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=ANY, offset=None, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_complete(self, test_instance: PublisherBacklistProcess, record_mappings):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings

        test_instance.process = 'complete'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=None, offset=None, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_custom(self, test_instance: PublisherBacklistProcess, record_mappings):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings
        
        test_instance.process = 'custom'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=None, offset=None, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_error(self, test_instance: PublisherBacklistProcess):
        test_instance.publisher_backlist_service.get_records.side_effect = Exception()

        test_instance.process = 'daily'

        with pytest.raises(Exception):
            test_instance.runProcess()

        test_instance.db_manager.close_connection.assert_called_once()
        test_instance.record_buffer.add.assert_not_called()
