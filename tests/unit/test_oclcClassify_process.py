import datetime
import os
import pytest

from tests.helper import TestHelpers
from processes import ClassifyProcess
from managers import ClassifyManager
from managers.oclcClassify import ClassifyError


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
                self.records = []
                self.ingestLimit = None
                self.rabbitQueue = os.environ['OCLC_QUEUE']
                self.rabbitRoute = os.environ['OCLC_ROUTING_KEY']
        
        return TestClassifyProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testRecord(self, mocker):
        mockRecord = mocker.MagicMock(name='testRecord')
        mockRecord.identifiers = ['1|test']
        mockRecord.authors = ['Author, Test|||true']
        mockRecord.title = 'Test Record'

        return mockRecord

    def test_runProcess_daily(self, testInstance, mocker):
        mockReceive = mocker.patch.object(ClassifyProcess, 'classifyRecords')
        mockSave = mocker.patch.object(ClassifyProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClassifyProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockReceive.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockReceive = mocker.patch.object(ClassifyProcess, 'classifyRecords')
        mockSave = mocker.patch.object(ClassifyProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClassifyProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockReceive.assert_called_once_with(full=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockReceive = mocker.patch.object(ClassifyProcess, 'classifyRecords')
        mockSave = mocker.patch.object(ClassifyProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClassifyProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testDate'
        testInstance.runProcess()

        mockReceive.assert_called_once_with(startDateTime='testDate')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_classifyRecords_not_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockQuery.yield_per.return_value = mockRecords
        testInstance.classifyRecords()

        mockSession.query.filter.assert_called_once
        mockDatetime.utcnow.assert_called_once
        mockDatetime.timedelta.assert_called_once
        mockQuery.filter.assert_called_once
        mockQuery.yield_per.assert_called_once_with(100)
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])

    def test_classifyRecords_custom_range(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockQuery.yield_per.return_value = mockRecords
        testInstance.classifyRecords(startDateTime='testDate')

        mockSession.query.filter.assert_called_once
        mockDatetime.utcnow.assert_not_called
        mockDatetime.timedelta.assert_not_called
        mockQuery.filter.assert_called_once
        mockQuery.yield_per.assert_called_once_with(100)
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])

    def test_classifyRecords_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockQuery.yield_per.return_value = mockRecords
        testInstance.classifyRecords(full=True)

        mockSession.query.filter.assert_called_once
        mockDatetime.utcnow.assert_not_called
        mockDatetime.timedelta.assert_not_called
        mockQuery.filter.assert_not_called
        mockQuery.yield_per.assert_called_once_with(100)
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])

    def test_classifyRecords_full_batch(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter.return_value = mockQuery
        mockRecords = [mocker.MagicMock(name=i) for i in range(100)]
        mockQuery.yield_per.return_value = mockRecords

        testInstance.ingestLimit = 100
        testInstance.classifyRecords(full=True)

        mockSession.query.filter.assert_called_once
        mockSession.query.limit.assert_called_once
        mockDatetime.utcnow.assert_not_called
        mockDatetime.timedelta.assert_not_called
        mockQuery.filter.assert_not_called

    def test_frbrizeRecord_success_valid_author(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classifyRecordByMetadata')

        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_called_once_with('1', 'test', 'Author, Test', 'Test Record')

    def test_frbrizeRecord_success_author_missing(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classifyRecordByMetadata')

        testRecord.authors = []
        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_called_once_with('1', 'test', None, 'Test Record')

    def test_frbrizeRecord_identifier_in_redis(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = True

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classifyRecordByMetadata')

        testRecord.authors = []
        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_not_called
        
    def test_classifyRecordByMetadata_success(self, testInstance, mocker):
        mockClassifier = mocker.patch('processes.oclcClassify.ClassifyManager')
        mockClassifierInstance = mocker.MagicMock()
        mockClassifier.return_value = mockClassifierInstance
        mockClassifierInstance.getClassifyResponse.return_value = [
            'xml1', 'xml2', 'xml3'
        ]

        mockCreateDCDW = mocker.patch.object(ClassifyProcess, 'createClassifyDCDWRecord')

        testInstance.classifyRecordByMetadata('1', 'test', 'testAuthor', 'testTitle')

        mockClassifier.assert_called_once_with(
            iden='1', idenType='test', author='testAuthor', title='testTitle'
        )
        mockClassifier.getClassifyResponse.assert_called_once

        mockCreateDCDW.assert_has_calls([
            mocker.call('xml1', '1', 'test'),
            mocker.call('xml2', '1', 'test'),
            mocker.call('xml3', '1', 'test')
        ])

    def test_classifyRecordByMetadata_error(self, testInstance, mocker):
        mockClassifier = mocker.patch('processes.oclcClassify.ClassifyManager')
        mockClassifierInstance = mocker.MagicMock()
        mockClassifier.return_value = mockClassifierInstance
        mockClassifierInstance.getClassifyResponse.side_effect = ClassifyError

        mockCreateDCDW = mocker.patch.object(ClassifyProcess, 'createClassifyDCDWRecord')

        with pytest.raises(ClassifyError):
            testInstance.classifyRecordByMetadata('1', 'test', 'testAuthor', 'testTitle')

    def test_createClassifyDCDWRecord(self, testInstance, mocker):
        mockMappingInstance = mocker.MagicMock()
        mockMappingInstance.record.identifiers = ['1|test', '2|test']
        mockMapping = mocker.patch('processes.oclcClassify.ClassifyMapping')
        mockMapping.return_value = mockMappingInstance

        mockAddDCDW = mocker.patch.object(ClassifyProcess, 'addDCDWToUpdateList')
        mockfetchOCLC = mocker.patch.object(ClassifyProcess, 'fetchOCLCCatalogRecords')

        testInstance.createClassifyDCDWRecord(('testXML', []), '1', 'test')

        mockMapping.assert_called_once_with(
            'testXML', {'oclc': 'http://classify.oclc.org'}, {}, ('1', 'test')
        )
        mockMappingInstance.applyMapping.assert_called_once()
        mockMappingInstance.extendIdentifiers.assert_called_once_with([])
        mockAddDCDW.assert_called_once_with(mockMappingInstance)
        mockfetchOCLC.assert_called_once_with(['1|test', '2|test'])

    def test_fetchOCLCCatalogRecords_no_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False
        mockSendLookup = mocker.patch.object(ClassifyProcess, 'sendCatalogLookupMessage')

        testInstance.fetchOCLCCatalogRecords(['1|test', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', '2', 'oclc')
        mockSendLookup.assert_called_once_with('2')

    def test_fetchOCLCCatalogRecords_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = True
        mockSendLookup = mocker.patch.object(ClassifyProcess, 'sendCatalogLookupMessage')

        testInstance.fetchOCLCCatalogRecords(['1|test', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', '2', 'oclc')
        mockSendLookup.assert_not_called
    
    def test_sendCatalogLookupMessage(self, testInstance, mocker):
        mockSendMessage = mocker.patch.object(ClassifyProcess, 'sendMessageToQueue')

        testInstance.sendCatalogLookupMessage('1')

        mockSendMessage.assert_called_once_with(
            'test_oclc_queue', 'test_oclc_key', {'oclcNo': '1'}
        )
