import datetime
import os
import pytest

from tests.helper import TestHelpers
from processes import ClassifyProcess

class TestOCLCClassifyProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def test_instance(self, mocker):
        class TestClassifyProcess(ClassifyProcess):
            def __init__(self, *args):
                self.records = set()
                self.ingest_limit = None
                self.records = []
                self.catalog_queue = os.environ['OCLC_QUEUE']
                self.catalog_route = os.environ['OCLC_ROUTING_KEY']
                self.classified_count = 0
                self.oclc_catalog_manager = mocker.MagicMock()
                self.rabbitmq_manager = mocker.MagicMock()
                self.redis_manager = mocker.MagicMock()

        return TestClassifyProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def run_process_mocks(self, mocker):
        return mocker.patch.multiple(
            ClassifyProcess,
            classify_records=mocker.DEFAULT,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT,
        )

    @pytest.fixture
    def test_record(self, mocker):
        mockRecord = mocker.MagicMock(name='test_record')
        mockRecord.identifiers = ['1|test']
        mockRecord.authors = ['Author, Test|||true']
        mockRecord.title = 'Test Record'

        return mockRecord

    def test_runProcess_daily(self, test_instance, run_process_mocks):
        test_instance.process = 'daily'
        test_instance.runProcess()

        for _, mockedMethod in run_process_mocks.items():
            mockedMethod.assert_called_once()

    def test_runProcess_complete(self, test_instance, run_process_mocks):
        test_instance.process = 'complete'
        test_instance.runProcess()

        run_process_mocks['classify_records'].assert_called_once_with(full=True)
        for _, mocked_method in run_process_mocks.items():
            mocked_method.assert_called_once()

    def test_runProcess_custom(self, test_instance, run_process_mocks):
        test_instance.process = 'custom'
        test_instance.ingestPeriod = 'testDate'
        test_instance.runProcess()

        run_process_mocks['classify_records'].assert_called_once_with(start_date_time='testDate')
        
        for _, mocked_method in run_process_mocks.items():
            mocked_method.assert_called_once()

    def test_classify_records_not_full(self, test_instance, mocker):
        mock_frbrize_record = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mock_session = mocker.MagicMock()
        mock_query = mocker.MagicMock()
        test_instance.session = mock_session

        mock_session.query().filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_records = [mocker.MagicMock(name=i) for i in range(100)]
        mock_query.first.side_effect = mock_records + [None]

        test_instance.redis_manager.checkIncrementerRedis.side_effect = [False] * 100

        test_instance.classify_records()

        mock_frbrize_record.assert_has_calls([mocker.call(record) for record in mock_records])

    def test_classify_records_custom_range(self, test_instance, mocker):
        mock_frbrize = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mock_session = mocker.MagicMock()
        mock_query = mocker.MagicMock()
        test_instance.session = mock_session
        mock_start_time = mocker.spy(datetime, 'datetime')

        mock_session.query().filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_records = [mocker.MagicMock(name=i) for i in range(100)]
        mock_query.first.side_effect = mock_records + [None]

        test_instance.redis_manager.checkIncrementerRedis.side_effect = [False] * 100

        test_instance.classify_records(start_date_time='testDate')

        mock_start_time.now.assert_not_called()
        mock_start_time.timedelta.assert_not_called()
        mock_frbrize.assert_has_calls([mocker.call(record) for record in mock_records])

    def test_classify_records_full(self, test_instance, mocker):
        mock_frbrize_record = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mock_session = mocker.MagicMock()
        mock_query = mocker.MagicMock()
        test_instance.session = mock_session
        mock_start_time = mocker.spy(datetime, 'datetime')

        mock_session.query().filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_records = [mocker.MagicMock(name=i) for i in range(100)]
        mock_query.first.side_effect = mock_records + [None]

        test_instance.redis_manager.checkIncrementerRedis.side_effect = [False] * 50 + [True]

        test_instance.classify_records(full=True)

        mock_start_time.now.assert_not_called()
        mock_start_time.timedelta.assert_not_called()
        mock_frbrize_record.assert_has_calls([mocker.call(record) for record in mock_records[:50]])

    def test_classify_records_full_batch(self, test_instance, mocker):
        mock_frbrize_record = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mock_session = mocker.MagicMock()
        mock_query = mocker.MagicMock()
        test_instance.session = mock_session
        mock_start_time = mocker.spy(datetime, 'datetime')

        mock_session.query().filter.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_records = [mocker.MagicMock(name=i) for i in range(100)]
        mock_query.first.side_effect = mock_records + [None]

        test_instance.redis_manager.checkIncrementerRedis.side_effect = [False] * 100

        test_instance.ingest_limit = 100
        test_instance.classify_records(full=True)

        mock_start_time.now.assert_not_called()
        mock_start_time.timedelta.assert_not_called()
        mock_frbrize_record.assert_has_calls([mocker.call(record) for record in mock_records])

    def test_frbrize_record_success_valid_author(self, test_instance, test_record, mocker):
        mock_identifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mock_identifiers.return_value = ['1|test']

        test_instance.redis_manager.checkSetRedis.return_value = False

        mock_classify_record = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        test_instance.frbrize_record(test_record)

        mock_identifiers.assert_called_once_with(test_record.identifiers)
        test_instance.redis_manager.checkSetRedis.assert_called_once_with('classify', '1', 'test')
        mock_classify_record.assert_called_once_with('1', 'test', 'Author, Test', 'Test Record')

    def test_frbrize_record_success_author_missing(self, test_instance, test_record, mocker):
        mock_identifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mock_identifiers.return_value = ['1|test']

        test_instance.redis_manager.checkSetRedis.return_value = False

        mock_classify_record = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        test_record.authors = []
        test_instance.frbrize_record(test_record)

        mock_identifiers.assert_called_once_with(test_record.identifiers)
        test_instance.redis_manager.checkSetRedis.assert_called_once_with('classify', '1', 'test')
        mock_classify_record.assert_called_once_with('1', 'test', None, 'Test Record')

    def test_frbrize_record_identifier_in_redis(self, test_instance, test_record, mocker):
        mock_identifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mock_identifiers.return_value = ['1|test']

        test_instance.redis_manager.checkSetRedis.return_value = True

        mock_classify_record = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        test_record.authors = []
        test_instance.frbrize_record(test_record)

        mock_identifiers.assert_called_once_with(test_record.identifiers)
        test_instance.redis_manager.checkSetRedis.assert_called_once_with('classify', '1', 'test')
        mock_classify_record.assert_not_called

    def test_frbrize_record_identifier_missing(self, test_instance, test_record, mocker):
        mock_identifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mock_identifiers.return_value = []
        mock_classify_record = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        test_instance.frbrize_record(test_record)

        mock_identifiers.assert_called_once_with(test_record.identifiers)
        test_instance.redis_manager.checkSetRedis.assert_not_called()
        mock_classify_record.assert_called_once_with(None, None, 'Author, Test', 'Test Record')

    def test_get_oclc_catalog_records_no_redis_match(self, test_instance, mocker):
        test_instance.redis_manager.multiCheckSetRedis.return_value = [('2', True)]

        test_instance.get_oclc_catalog_records(['1|owi', '2|oclc'])

        test_instance.redis_manager.multiCheckSetRedis.assert_called_once_with('catalog', ['2'], 'oclc')
        test_instance.rabbitmq_manager.sendMessageToQueue.assert_called_once_with('test_oclc_queue', 'test_oclc_key', {'oclcNo': '2', 'owiNo': '1'})
        test_instance.redis_manager.setIncrementerRedis.assert_called_once_with('oclcCatalog', 'API', amount=1)

    def test_get_oclc_catalog_records_redis_match(self, test_instance, mocker):
        test_instance.redis_manager.multiCheckSetRedis.return_value = [(2, False)]

        test_instance.get_oclc_catalog_records(['1|test', '2|oclc'])

        test_instance.redis_manager.multiCheckSetRedis.assert_called_once_with('catalog', ['2'], 'oclc')
        test_instance.rabbitmq_manager.sendMessageToQueue.assert_not_called()
        test_instance.redis_manager.setIncrementerReids.assert_not_called()
    
    def test_get_queryable_identifiers(self, test_instance):
        assert test_instance._get_queryable_identifiers(['1|isbn', '2|test']) == ['1|isbn']
