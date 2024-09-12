import datetime
from lxml import etree
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
                self.records = set()
                self.classifiedRecords = {}
                self.ingestLimit = None
                self.rabbitQueue = os.environ['OCLC_QUEUE']
                self.rabbitRoute = os.environ['OCLC_ROUTING_KEY']
                self.oclc_catalog_manager = mocker.MagicMock()
        
        return TestClassifyProcess('TestProcess', 'testFile', 'testDate')
    
    @pytest.fixture
    def testXMLResponse(self):
        def constructResponse(code, responseBlock):
            return etree.fromstring('''<?xml version="1.0"?>
                <classify xmlns="http://classify.oclc.org" xmlns:oclc="http://classify.oclc.org">
                    <response code="{}"/>
                    {}
                </classify>
            '''.format(code, responseBlock))
        
        return constructResponse

    @pytest.fixture
    def runProcessMocks(self, mocker):
        return mocker.patch.multiple(
            ClassifyProcess,
            classifyRecords=mocker.DEFAULT,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT,
            updateClassifiedRecordsStatus=mocker.DEFAULT
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

        runProcessMocks['classifyRecords'].assert_called_once_with(full=True)
        for _, mockedMethod in runProcessMocks.items():
            mockedMethod.assert_called_once()

    def test_runProcess_custom(self, testInstance, runProcessMocks):
        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testDate'
        testInstance.runProcess()

        runProcessMocks['classifyRecords'].assert_called_once_with(startDateTime='testDate')
        for _, mockedMethod in runProcessMocks.items():
            mockedMethod.assert_called_once()

    def test_classifyRecords_not_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
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

        mockUpdateClassified = mocker.patch.object(ClassifyProcess, 'updateClassifiedRecordsStatus')

        testInstance.classifyRecords()

        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mockUpdateClassified.assert_called_once()

    def test_classifyRecords_custom_range(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
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

        mockUpdateClassified = mocker.patch.object(ClassifyProcess, 'updateClassifiedRecordsStatus')

        testInstance.classifyRecords(startDateTime='testDate')

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mockUpdateClassified.assert_called_once()

    def test_classifyRecords_full(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
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

        mockUpdateClassified = mocker.patch.object(ClassifyProcess, 'updateClassifiedRecordsStatus')

        testInstance.classifyRecords(full=True)

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockWindowed.assert_called_once()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords[:50]])
        mockUpdateClassified.assert_not_called()

    def test_classifyRecords_full_batch(self, testInstance, mocker):
        mockFrbrize = mocker.patch.object(ClassifyProcess, 'frbrizeRecord')
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

        mockUpdateClassified = mocker.patch.object(ClassifyProcess, 'updateClassifiedRecordsStatus')

        testInstance.ingestLimit = 100
        testInstance.classifyRecords(full=True)

        mockDatetime.now.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockFrbrize.assert_has_calls([mocker.call(rec) for rec in mockRecords])
        mockUpdateClassified.assert_called_once()

    def test_updateClassifiedRecordsStatus(self, testInstance, mocker):
        mockBulkSave = mocker.patch.object(ClassifyProcess, 'bulkSaveObjects')

        testInstance.classifiedRecords = {1: 'rec1', 2: 'rec2', 3: 'rec3'}
        testInstance.updateClassifiedRecordsStatus()

        mockBulkSave.assert_called_once_with(['rec1', 'rec2', 'rec3'])

    def test_frbrizeRecord_success_valid_author(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata_v2')

        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_called_once_with('1', 'test', 'Author, Test', 'Test Record')

    def test_frbrizeRecord_success_author_missing(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = ['1|test']

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockRedisCheck.return_value = False

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata_v2')

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

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata_v2')

        testRecord.authors = []
        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_called_once_with('classify', '1', 'test')
        mockClassifyRec.assert_not_called

    def test_frbrizeRecord_identifier_missing(self, testInstance, testRecord, mocker):
        mockIdentifiers = mocker.patch.object(ClassifyManager, 'getQueryableIdentifiers')
        mockIdentifiers.return_value = []

        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'checkSetRedis')

        mockClassifyRec = mocker.patch.object(ClassifyProcess, 'classify_record_by_metadata_v2')

        testInstance.frbrizeRecord(testRecord)

        mockIdentifiers.assert_called_once_with(testRecord.identifiers)
        mockRedisCheck.assert_not_called()
        mockClassifyRec.assert_called_once_with(None, None, 'Author, Test', 'Test Record')
        
    def test_classifyRecordByMetadata_success(self, testInstance, mocker):
        mockClassifier = mocker.patch('processes.oclcClassify.ClassifyManager')
        mockClassifierInstance = mocker.MagicMock(addlIds=[])
        mockClassifier.return_value = mockClassifierInstance
        mockClassifierInstance.getClassifyResponse.return_value = [
            'xml1', 'xml2', 'xml3'
        ]

        mockCheckFetched = mocker.patch.object(ClassifyProcess, 'checkIfClassifyWorkFetched')
        mockCheckFetched.side_effect = [False, True, False]
        mockCreateDCDW = mocker.patch.object(ClassifyProcess, 'createClassifyDCDWRecord')

        testInstance.classifyRecordByMetadata('1', 'test', 'testAuthor', 'testTitle')

        mockClassifier.assert_called_once_with(
            iden='1', idenType='test', author='testAuthor', title='testTitle'
        )

        mockClassifierInstance.getClassifyResponse.assert_called_once()

        mockCheckFetched.assert_has_calls([
            mocker.call('xml1'), mocker.call('xml2'), mocker.call('xml3')
        ])

        mockClassifierInstance.checkAndFetchAdditionalEditions.assert_has_calls([
            mocker.call('xml1'), mocker.call('xml3')
        ])

        mockCreateDCDW.assert_has_calls([
            mocker.call('xml1', [], '1', 'test'), mocker.call('xml3', [], '1', 'test')
        ])

    def test_classifyRecordByMetadata_error(self, testInstance, mocker):
        mockClassifier = mocker.patch('processes.oclcClassify.ClassifyManager')
        mockClassifierInstance = mocker.MagicMock()
        mockClassifier.return_value = mockClassifierInstance
        mockClassifierInstance.getClassifyResponse.side_effect = ClassifyError

        mocker.patch.object(ClassifyProcess, 'createClassifyDCDWRecord')

        with pytest.raises(ClassifyError):
            testInstance.classifyRecordByMetadata('1', 'test', 'testAuthor', 'testTitle')

    def test_createClassifyDCDWRecord(self, testInstance, mocker):
        mockMappingInstance = mocker.MagicMock()
        mockMappingInstance.record.identifiers = ['1|test', '2|test']
        mockMapping = mocker.patch('processes.oclcClassify.ClassifyMapping')
        mockMapping.return_value = mockMappingInstance

        mockAddDCDW = mocker.patch.object(ClassifyProcess, 'addDCDWToUpdateList')
        mockfetchOCLC = mocker.patch.object(ClassifyProcess, 'fetchOCLCCatalogRecords')

        testInstance.createClassifyDCDWRecord('testXML', [], '1', 'test')

        mockMapping.assert_called_once_with(
            'testXML', {'oclc': 'http://classify.oclc.org'}, {}, ('1', 'test')
        )
        mockMappingInstance.applyMapping.assert_called_once()
        mockMappingInstance.extendIdentifiers.assert_called_once_with([])
        mockAddDCDW.assert_called_once_with(mockMappingInstance)
        mockfetchOCLC.assert_called_once_with(['1|test', '2|test'])

    def test_fetchOCLCCatalogRecords_no_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'multiCheckSetRedis')
        mockRedisCheck.return_value = [('2', True)]
        mockSendLookup = mocker.patch.object(ClassifyProcess, 'sendCatalogLookupMessage')
        mockSetRedis = mocker.patch.object(ClassifyProcess, 'setIncrementerRedis')

        testInstance.fetchOCLCCatalogRecords(['1|owi', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', ['2'], 'oclc')
        mockSendLookup.assert_called_once_with('2', '1')
        mockSetRedis.assert_called_once_with('oclcCatalog', 'API', amount=1)

    def test_fetchOCLCCatalogRecords_redis_match(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClassifyProcess, 'multiCheckSetRedis')
        mockRedisCheck.return_value = [(2, False)]
        mockSendLookup = mocker.patch.object(ClassifyProcess, 'sendCatalogLookupMessage')
        mockSetRedis = mocker.patch.object(ClassifyProcess, 'setIncrementerRedis')

        testInstance.fetchOCLCCatalogRecords(['1|test', '2|oclc'])

        mockRedisCheck.assert_called_once_with('catalog', ['2'], 'oclc')
        mockSendLookup.assert_not_called()
        mockSetRedis.assert_not_called()
    
    def test_sendCatalogLookupMessage(self, testInstance, mocker):
        mockSendMessage = mocker.patch.object(ClassifyProcess, 'sendMessageToQueue')

        testInstance.sendCatalogLookupMessage('1', '1')

        mockSendMessage.assert_called_once_with(
            'test_oclc_queue', 'test_oclc_key', {'oclcNo': '1', 'owiNo': '1'}
        )

    def test_checkIfClassifyWorkFetched(self, testInstance, testXMLResponse, mocker):
        testXML = testXMLResponse(2, '<work owi="1"/>')

        mockCheckRedis = mocker.patch.object(ClassifyProcess, 'checkSetRedis')
        mockCheckRedis.return_value = False

        assert testInstance.checkIfClassifyWorkFetched(testXML) == False

        mockCheckRedis.assert_called_once_with('classifyWork', '1', 'owi')
