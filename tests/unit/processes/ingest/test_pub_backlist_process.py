import pytest

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
                self.offset = None
                self.limit = None
                self.ingestPeriod = None
                self.records = []
        
        return TestPublisherBacklistProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def mocks(self, mocker):
        return {
            'generate_engine': mocker.patch.object(PublisherBacklistProcess, 'generateEngine'),
            'create_session': mocker.patch.object(PublisherBacklistProcess, 'createSession'),
            'save': mocker.patch.object(PublisherBacklistProcess, 'saveRecords'),
            'commit': mocker.patch.object(PublisherBacklistProcess, 'commitChanges'),
            'close': mocker.patch.object(PublisherBacklistProcess, 'close_connection'),
            'add_record': mocker.patch.object(PublisherBacklistProcess, 'addDCDWToUpdateList')
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
    
    def test_runProcess_daily(self, test_instance: PublisherBacklistProcess, record_mappings, mocks):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings

        test_instance.process = 'daily'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(offset=None, limit=None)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_complete(self, test_instance: PublisherBacklistProcess, record_mappings, mocks):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings

        test_instance.process = 'complete'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(full_import=True)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_custom(self, test_instance: PublisherBacklistProcess, record_mappings, mocks):
        test_instance.publisher_backlist_service.get_records.return_value = record_mappings
        
        test_instance.process = 'custom'
        test_instance.runProcess()

        test_instance.publisher_backlist_service.get_records.assert_called_once_with(start_timestamp=None, offset=None, limit=None)
        self.assert_common_expectations(mocks)
        assert mocks['add_record'].call_count == len(record_mappings)

    def test_runProcess_unknown(self, test_instance: PublisherBacklistProcess, mocks):
        test_instance.process = 'unknown'
        test_instance.runProcess()
        
        test_instance.publisher_backlist_service.get_records.assert_not_called()

        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['commit'].assert_not_called()
        mocks['save'].assert_not_called()
        mocks['add_record'].assert_not_called()
        mocks['close'].assert_called_once()

    def test_runProcess_error(self, test_instance: PublisherBacklistProcess, mocks):
        test_instance.publisher_backlist_service.get_records.side_effect = Exception()

        test_instance.process = 'daily'

        with pytest.raises(Exception):
            test_instance.runProcess()

        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['commit'].assert_not_called()
        mocks['save'].assert_not_called()
        mocks['add_record'].assert_not_called()
        mocks['close'].assert_called_once()
