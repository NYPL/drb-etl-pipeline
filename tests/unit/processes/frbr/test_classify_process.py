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
    def testInstance(self, mocker):
        class TestClassifyProcess(ClassifyProcess):
            def __init__(self, *args):
                self.records = set()
                self.ingest_limit = None
                self.records = []
                self.catalog_queue = os.environ['OCLC_QUEUE']
                self.catalog_route = os.environ['OCLC_ROUTING_KEY']
                self.classified_count = 0
                self.oclc_catalog_manager = mocker.MagicMock()

        return TestClassifyProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def runProcessMocks(self, mocker):
        return mocker.patch.multiple(
            ClassifyProcess,
            classify_records=mocker.DEFAULT,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT,
        )

    @pytest.fixture
    def testRecord(self, mocker):
        mockRecord = mocker.MagicMock(name='testRecord')
        mockRecord.identifiers = ['1|test']
        mockRecord.authors = ['Author, Test|||true']
        mockRecord.title = 'Test Record'

        return mockRecord

    def test_runProcess_daily(self, testInstance, runProcessMocks):
        testInstance.process = 'daily'
        testInstance.runProcess()

        for _, mockedMethod in runProcessMocks.items():
            mockedMethod.assert_called_once()

    def test_runProcess_complete(self, testInstance, runProcessMocks):
        testInstance.process = 'complete'
        testInstance.runProcess()

        runProcessMocks['classify_records'].assert_called_once_with(full=True)
        for _, mockedMethod in runProcessMocks.items():
            mockedMethod.assert_called_once()

    def test_runProcess_custom(self, testInstance, runProcessMocks):
        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testDate'
        testInstance.runProcess()

        runProcessMocks['classify_records'].assert_called_once_with(start_date_time='testDate')
        
        for _, mockedMethod in runProcessMocks.items():
            mockedMethod.assert_called_once()

    def test_classify_records_not_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession

        mockSession.query().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockWindowed = mocker.patch.object(ClassifyProcess, 'windowedQuery')
        mockWindowed.return_value = mockRecords

        mockOCLCCheck = mocker.patch.object(ClassifyProcess, 'checkIncrementerRedis')
        mockOCLCCheck.side_effect = [False] * 100

        mock_bulk_save_objects = mocker.patch.object(ClassifyProcess, 'bulkSaveObjects')

        testInstance.classify_records()

        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mock_bulk_save_objects.assert_called_once()

    def test_classify_records_custom_range(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockWindowed = mocker.patch.object(ClassifyProcess, 'windowedQuery')
        mockWindowed.return_value = mockRecords

        mockOCLCCheck = mocker.patch.object(ClassifyProcess, 'checkIncrementerRedis')
        mockOCLCCheck.side_effect = [False] * 100

        mock_bulk_save_objects = mocker.patch.object(ClassifyProcess, 'bulkSaveObjects')

        testInstance.classify_records(start_date_time='testDate')

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mock_bulk_save_objects.assert_called_once()

    def test_classify_records_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockWindowed = mocker.patch.object(ClassifyProcess, 'windowedQuery')
        mockWindowed.return_value = mockRecords

        mockOCLCCheck = mocker.patch.object(ClassifyProcess, 'checkIncrementerRedis')
        mockOCLCCheck.side_effect = [False] * 50 + [True]

        mock_bulk_save_objects = mocker.patch.object(ClassifyProcess, 'bulkSaveObjects')

        testInstance.classify_records(full=True)

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords[:50]])
        mock_bulk_save_objects.assert_not_called()

    def test_classify_records_full_batch(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrize_record')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockWindowed = mocker.patch.object(ClassifyProcess, 'windowedQuery')
        mockWindowed.return_value = mockRecords

        mockOCLCCheck = mocker.patch.object(ClassifyProcess, 'checkIncrementerRedis')
        mockOCLCCheck.side_effect = [False] * 100

        mock_bulk_save_objects = mocker.patch.object(ClassifyProcess, 'bulkSaveObjects')

        testInstance.ingestLimit = 100
        testInstance.classify_records(full=True)

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mock_bulk_save_objects.assert_called_once()

    def test_frbrize_record_success_valid_author(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        testInstance.frbrize_record(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_called_once_with('1', 'test', 'Author, Test', 'Test Record')

    def test_frbrize_record_success_author_missing(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        testRecord.authors = []
        testInstance.frbrize_record(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_called_once_with('1', 'test', None, 'Test Record')

    def test_frbrize_record_identifier_in_redis(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = True

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        testRecord.authors = []
        testInstance.frbrize_record(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_not_called

    def test_frbrize_record_identifier_missing(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyProcess, '_get_queryable_identifiers')
        mockIdentifiers.return_value = []
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata')

        testInstance.frbrize_record(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_not_called()
        mockClassifyRec.assert_called_once_with(None, None, 'Author, Test', 'Test Record')

    def test_get_oclc_catalog_records_no_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'multiCheckSetRedis')
        mockRedisCheck.return_value = [('2', True)]
        mock_send_message_to_queue = mocker.patch.object(ClassifyProcess, 'sendMessageToQueue')
        mockSetRedis = mocker.patch.object(ClassifyProcess, 'setIncrementerRedis')

        testInstance.get_oclc_catalog_records(['1|owi', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', ['2'], 'oclc')
        mock_send_message_to_queue.assert_called_once_with('test_oclc_queue', 'test_oclc_key', {'oclcNo': '2', 'owiNo': '1'})
        mockSetRedis.assert_called_once_with('oclcCatalog', 'API', amount=1)

    def test_get_oclc_catalog_records_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'multiCheckSetRedis')
        mockRedisCheck.return_value = [(2, False)]
        mock_send_message_to_queue = mocker.patch.object(ClassifyProcess, 'sendMessageToQueue')
        mockSetRedis = mocker.patch.object(ClassifyProcess, 'setIncrementerRedis')

        testInstance.get_oclc_catalog_records(['1|test', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', ['2'], 'oclc')
        mock_send_message_to_queue.assert_not_called()
        mockSetRedis.assert_not_called()
    
    def test_get_queryable_identifiers(self, testInstance):
        assert testInstance._get_queryable_identifiers(['1|isbn', '2|test']) == ['1|isbn']
