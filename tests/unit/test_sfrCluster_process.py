import datetime
from processes.sfrCluster import ClusterError
import pytest

from tests.helper import TestHelpers
from processes import ClusterProcess
from model import Record


class TestSFRClusterProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestClusterProcess(ClusterProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.records = []
                self.statics = {'iso639': {}}
        
        return TestClusterProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testRecord(self, mocker):
        return mocker.MagicMock(id=1, title='Test', identifiers=['1|test'], uuid='testUUID')

    def test_runProcess_daily(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecords')
        mockSave = mocker.patch.object(ClusterProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClusterProcess, 'commitChanges')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockCluster.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecords')
        mockSave = mocker.patch.object(ClusterProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClusterProcess, 'commitChanges')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockCluster.assert_called_once_with(full=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecords')
        mockSave = mocker.patch.object(ClusterProcess, 'saveRecords')
        mockCommit = mocker.patch.object(ClusterProcess, 'commitChanges')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testDate'
        testInstance.runProcess()

        mockCluster.assert_called_once_with(startDateTime='testDate')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_clusterRecords_not_full(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecord')
        mockClose = mocker.patch.object(ClusterProcess, 'closeConnection')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.first.side_effect = ['rec1', 'rec2', None]

        testInstance.clusterRecords()

        mockSession.query.filter.filter.assert_called_once
        mockDatetime.utcnow.assert_called_once
        mockDatetime.timedelta.assert_called_once
        mockQuery.filter.assert_called_once
        assert mockQuery.first.call_count == 3
        mockCluster.assert_has_calls([mocker.call('rec1'), mocker.call('rec2')])
        mockClose.assert_called_once

    def test_clusterRecords_custom_range(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecord')
        mockClose = mocker.patch.object(ClusterProcess, 'closeConnection')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.first.side_effect = ['rec1', 'rec2', None]

        testInstance.clusterRecords(startDateTime='testDate')

        mockSession.query.filter.filter.assert_called_once
        mockDatetime.utcnow.assert_not_called
        mockDatetime.timedelta.assert_not_called
        mockQuery.filter.assert_called_once
        assert mockQuery.first.call_count == 3
        mockCluster.assert_has_calls([mocker.call('rec1'), mocker.call('rec2')])
        mockClose.assert_called_once

    def test_clusterRecords_full(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'clusterRecord')
        mockClose = mocker.patch.object(ClusterProcess, 'closeConnection')
        mockUpdate = mocker.patch.object(ClusterProcess, 'updateMatchedRecordsStatus')
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter().filter.return_value = mockQuery
        mockQueryResponses = [mocker.MagicMock(id=1), mocker.MagicMock(id=2), None]
        mockQuery.first.side_effect = mockQueryResponses

        mockCluster.side_effect = [None, ClusterError]

        testInstance.clusterRecords(full=True)

        mockSession.query().filter().filter.assert_called_once()
        mockDatetime.utcnow.assert_not_called()
        mockDatetime.timedelta.assert_not_called()
        mockQuery.filter.assert_not_called()
        assert mockQuery.first.call_count == 3
        mockCluster.assert_has_calls(mockQuery[:1])
        mockUpdate.assert_called_once_with([2])
        mockClose.assert_called_once()

    def test_clusterRecord_w_matching_records(self, testInstance, testRecord, mocker):
        clusterMocks = mocker.patch.multiple(ClusterProcess,
            tokenizeTitle=mocker.DEFAULT,
            findAllMatchingRecords=mocker.DEFAULT,
            clusterMatchedRecords=mocker.DEFAULT,
            createWorkFromEditions=mocker.DEFAULT,
            indexWorkInElasticSearch=mocker.DEFAULT,
            updateMatchedRecordsStatus=mocker.DEFAULT
        )
        clusterMocks['findAllMatchingRecords'].return_value = ['3|test']
        clusterMocks['clusterMatchedRecords'].return_value = (['ed1', 'ed2'], ['inst1', 'inst2', 'inst3'])
        clusterMocks['createWorkFromEditions'].return_value = 'testDBWork'
        clusterMocks['tokenizeTitle'].return_value = set(['test', 'title'])

        mockSession = mocker.MagicMock()
        testInstance.session = mockSession
        testInstance.clusterRecord(testRecord)

        clusterMocks['tokenizeTitle'].assert_called_once_with('Test')
        assert testInstance.matchTitleTokens == set(['test', 'title'])
        clusterMocks['findAllMatchingRecords'].assert_called_once_with(['1|test'])
        clusterMocks['clusterMatchedRecords'].assert_called_once_with(['3|test'])
        clusterMocks['createWorkFromEditions'].assert_called_once_with(
            ['ed1', 'ed2'], ['inst1', 'inst2', 'inst3']
        )
        clusterMocks['indexWorkInElasticSearch'].assert_called_once_with('testDBWork')
        mockSession.flush.assert_called_once()
        clusterMocks['updateMatchedRecordsStatus'].assert_called_once_with(['3|test'])

    def test_clusterRecord_wo_matching_records(self, testInstance, testRecord, mocker):
        clusterMocks = mocker.patch.multiple(ClusterProcess,
            tokenizeTitle=mocker.DEFAULT,
            findAllMatchingRecords=mocker.DEFAULT,
            clusterMatchedRecords=mocker.DEFAULT,
            createWorkFromEditions=mocker.DEFAULT,
            indexWorkInElasticSearch=mocker.DEFAULT,
            updateMatchedRecordsStatus=mocker.DEFAULT
        )
        clusterMocks['findAllMatchingRecords'].return_value = []
        clusterMocks['clusterMatchedRecords'].return_value = (['ed1'], ['inst1'])
        clusterMocks['createWorkFromEditions'].return_value = 'testDBWork'
        clusterMocks['tokenizeTitle'].return_value = set(['test', 'title'])

        mockSession = mocker.MagicMock()
        testInstance.session = mockSession
        testInstance.clusterRecord(testRecord)

        clusterMocks['tokenizeTitle'].assert_called_once_with('Test')
        assert testInstance.matchTitleTokens == set(['test', 'title'])
        clusterMocks['findAllMatchingRecords'].assert_called_once_with(['1|test'])
        clusterMocks['clusterMatchedRecords'].assert_called_once_with([1])
        clusterMocks['createWorkFromEditions'].assert_called_once_with(['ed1'], ['inst1'])
        clusterMocks['indexWorkInElasticSearch'].assert_called_once_with('testDBWork')
        mockSession.flush.assert_called_once()
        clusterMocks['updateMatchedRecordsStatus'].assert_called_once_with([1])

    def test_updateMatchedRecordsStatus(self, testInstance, mocker):
        mockBulkSave = mocker.patch.object(ClusterProcess, 'bulkSaveObjects')

        mockRecord = mocker.MagicMock()
        mockSession = mocker.MagicMock()
        mockSession.query().filter().all.return_value = [mockRecord]
        testInstance.session = mockSession

        testInstance.updateMatchedRecordsStatus([1])

        assert mockRecord.cluster_status == True
        assert mockRecord.frbr_status == 'complete'
        mockSession.query().filter().all.assert_called_once()
        mockBulkSave.assert_called_once_with([mockRecord])

    def test_clusterMatchedRecords(self, testInstance, mocker):
        mockMLModel = mocker.MagicMock()
        mockMLModel.parseEditions.return_value = ['ed1', 'ed2']
        mockKManager = mocker.patch('processes.sfrCluster.KMeansManager')
        mockKManager.return_value = mockMLModel

        mockSession = mocker.MagicMock()
        mockSession.query().filter().all.return_value = ['rec1', 'rec2', 'rec3']
        testInstance.session = mockSession
        testEditions, testRecords = testInstance.clusterMatchedRecords([1, 2, 3]) 

        assert testEditions == ['ed1', 'ed2']
        assert testRecords == ['rec1', 'rec2', 'rec3']

        mockSession.query.filter.all.assert_called_once
        mockKManager.assert_called_once_with(['rec1', 'rec2', 'rec3'])
        mockMLModel.createDF.assert_called_once
        mockMLModel.generateClusters.assert_called_once
        mockMLModel.parseEditions.assert_called_once

    def test_findAllMatchingRecords(self, testInstance, mocker):
        mockIDQuery = mocker.patch.object(ClusterProcess, 'queryIdens')
        mockIDQuery.return_value = ['rec1', 'rec2']

        testRecords = testInstance.findAllMatchingRecords(['1|lcc', '2|oclc'])

        assert testRecords == ['rec1', 'rec2']
        mockIDQuery.assert_called_once_with(['2|oclc'])

    def test_createWorkFromEditions(self, testInstance, mocker):
        mockRecManager = mocker.MagicMock()
        mockRecManager.buildWork.return_value = 'testWorkData'
        mockRecManager.work = 'testWork'
        mockManagerInst = mocker.patch('processes.sfrCluster.SFRRecordManager')
        mockManagerInst.return_value = mockRecManager

        testInstance.session = 'testSession'
        testWork = testInstance.createWorkFromEditions('testEditions', 'testInstances')

        assert testWork == 'testWork'
        mockManagerInst.assert_called_once_with('testSession', {})
        mockRecManager.buildWork.assert_called_once_with('testInstances', 'testEditions')
        mockRecManager.saveWork.assert_called_once_with('testWorkData')
        mockRecManager.mergeRecords.assert_called_once()

    def test_queryIdens_success(self, testInstance, mocker):
        mockGetBatches = mocker.patch.object(ClusterProcess, 'getRecordBatches')
        mockGetBatches.side_effect = [
            [('title1', 1, ['1|isbn']), ('title2', 2, ['2|oclc', '3|other'])],
            [('title3', 3, ['4|oclc'])],
            []
        ]

        mockCompareTitles = mocker.patch.object(ClusterProcess, 'compareTitleTokens')
        mockCompareTitles.return_value = True

        testIDs = testInstance.queryIdens(['1|test', '2|test', '3|test'])

        assert testIDs == [1, 2]
        assert mockGetBatches.call_count == 3
        mockCompareTitles.assert_called_once_with('title3')

    def test_queryIdens_exceed_cluster_threshold(self, testInstance, mocker):
        mockGetBatch = mocker.patch.object(ClusterProcess, 'getRecordBatches')
        mockGetBatch.side_effect = [
            [('title{}'.format(i), i, ['{}|test'.format(i)]) for i in range(10001)],
            []
        ]

        with pytest.raises(Exception):
            testInstance.queryIdens(['1|oclc', '2|oclc', '3|oclc'])

    def test_getRecordBatches(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        mockFormatArray = mocker.patch.object(ClusterProcess, 'formatIdenArray')
        mockFormatArray.return_value = 'testIdentifierArray'

        testInstance.session.query().filter().filter().all.side_effect = [[1], [2, 3]]

        testMatches = testInstance.getRecordBatches([str(i) for i in range(103)], set([]))

        assert testMatches == [1, 2, 3]
        testInstance.session.query().filter.call_args[0][0].compare(~Record.id.in_([]))

        testInstance.session.query().filter().filter.call_args[0][0].compare(Record.identifiers.overlap('testIdentifierArray'))

    def test_indexWorkInElasticSearch(self, testInstance, mocker):
        mockElasticInst = mocker.patch('processes.sfrCluster.SFRElasticRecordManager')
        mockESManager = mocker.MagicMock()
        mockElasticInst.return_value = mockESManager

        testInstance.indexWorkInElasticSearch('testDBWork')

        mockElasticInst.assert_called_once_with('testDBWork')
        mockESManager.getCReateWork.assert_called_once
        mockESManager.saveWork.assert_called_once

    def test_formatIdenArray(self):
        assert ClusterProcess.formatIdenArray(['{test}|test', 'multi,test|test'])\
            == '{"{test}|test","multi,test|test"}'

    def test_tokenizeTitle_success(self):
        assert ClusterProcess.tokenizeTitle('A Test Title') == set(['test', 'title'])

    def test_tokenizeTitle_error(self):
        with pytest.raises(ClusterError):
            ClusterProcess.tokenizeTitle(None)
