import dateutil
import dateutil.parser
import pytest
from unittest.mock import ANY

from tests.helper import TestHelpers
from processes import PublisherBacklistProcess
from processes.utils import ProcessParams


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
                self.params = ProcessParams()
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

        test_instance.params.process_type = 'daily'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=ANY, offset=0, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_complete(self, test_instance: PublisherBacklistProcess, record_mappings):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings

        test_instance.params.process_type = 'complete'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=None, offset=0, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_custom(self, test_instance: PublisherBacklistProcess, record_mappings):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings
        
        test_instance.params.ingest_period = '2021-01-01T12:00:00'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=dateutil.parser.parse(test_instance.params.ingest_period), offset=0, limit=None)
        test_instance.record_buffer.add.call_count = len(record_mappings)
        test_instance.db_manager.close_connection.assert_called_once()

    def test_runProcess_error(self, test_instance: PublisherBacklistProcess):
        test_instance.publisher_backlist_service.get_records.side_effect = Exception()

        test_instance.process = 'daily'

        with pytest.raises(Exception):
            test_instance.runProcess()

        test_instance.db_manager.close_connection.assert_called_once()
        test_instance.record_buffer.add.assert_not_called()
