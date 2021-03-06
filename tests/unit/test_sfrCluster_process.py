import datetime
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
        
        return TestClusterProcess('TestProcess', 'testFile', 'testDate')

    @pytest.fixture
    def testRecord(self, mocker):
        return mocker.MagicMock(id=1, identifiers=['1|test'], uuid='testUUID')

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
        mockSession = mocker.MagicMock()
        mockQuery = mocker.MagicMock()
        testInstance.session = mockSession
        mockDatetime = mocker.spy(datetime, 'datetime')

        mockSession.query().filter().filter.return_value = mockQuery
        mockQuery.first.side_effect = ['rec1', 'rec2', None]

        testInstance.clusterRecords(full=True)

        mockSession.query.filter.filter.assert_called_once
        mockDatetime.utcnow.assert_not_called
        mockDatetime.timedelta.assert_not_called
        mockQuery.filter.assert_not_called
        assert mockQuery.first.call_count == 3
        mockCluster.assert_has_calls([mocker.call('rec1'), mocker.call('rec2')])
        mockClose.assert_called_once

    def test_clusterRecord_w_matching_records(self, testInstance, testRecord, mocker):
        mockFindMatching = mocker.patch.object(ClusterProcess, 'findAllMatchingRecords')
        mockFindMatching.return_value = ['3|test']
        mockClusterMatched = mocker.patch.object(ClusterProcess, 'clusterMatchedRecords')
        mockClusterMatched.return_value = (['ed1', 'ed2'], ['inst1', 'inst2', 'inst3'])
        mockCreateFromEds = mocker.patch.object(ClusterProcess, 'createWorkFromEditions')
        mockCreateFromEds.return_value = 'testDBWork'
        mockIndexInES = mocker.patch.object(ClusterProcess, 'indexWorkInElasticSearch')
        mockCommit = mocker.patch.object(ClusterProcess, 'commitChanges')

        mockSession = mocker.MagicMock()
        testInstance.session = mockSession
        testInstance.clusterRecord(testRecord)

        mockFindMatching.assert_called_once_with(['1|test'])
        mockClusterMatched.assert_called_once_with(['3|test'])
        mockCreateFromEds.assert_called_once_with(
            ['ed1', 'ed2'], ['inst1', 'inst2', 'inst3']
        )
        mockIndexInES.assert_called_once_with('testDBWork')
        mockSession.flush.assert_called_once()
        mockSession.query.assert_called_once()
        mockCommit.assert_called_once()

    def test_clusterRecord_wo_matching_records(self, testInstance, testRecord, mocker):
        mockFindMatching = mocker.patch.object(ClusterProcess, 'findAllMatchingRecords')
        mockFindMatching.return_value = []
        mockClusterMatched = mocker.patch.object(ClusterProcess, 'clusterMatchedRecords')
        mockClusterMatched.return_value = (['ed1'], ['inst1'])
        mockCreateFromEds = mocker.patch.object(ClusterProcess, 'createWorkFromEditions')
        mockCreateFromEds.return_value = 'testDBWork'
        mockIndexInES = mocker.patch.object(ClusterProcess, 'indexWorkInElasticSearch')
        mockCommit = mocker.patch.object(ClusterProcess, 'commitChanges')

        mockSession = mocker.MagicMock()
        testInstance.session = mockSession
        testInstance.clusterRecord(testRecord)

        mockFindMatching.assert_called_once_with(['1|test'])
        mockClusterMatched.assert_called_once_with([1])
        mockCreateFromEds.assert_called_once_with(['ed1'], ['inst1'])
        mockIndexInES.assert_called_once_with('testDBWork')
        mockSession.flush.assert_called_once()
        mockSession.query.assert_called_once()
        mockCommit.assert_called_once()

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
        mockManagerInst.assert_called_once_with('testSession')
        mockRecManager.buildWork.assert_called_once_with('testInstances', 'testEditions')
        mockRecManager.saveWork.assert_called_once_with('testWorkData')
        mockRecManager.assert_called_once

    def test_queryIdens_no_queryable_ids(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClusterProcess, 'checkSetRedis')
        mockRedisCheck.side_effect = [True, True, True]

        testIDs = testInstance.queryIdens(['1|test', '2|test', '3|test'])

        assert testIDs == []
        mockRedisCheck.assert_has_calls([
            mocker.call('cluster', '1|test', 'all'),
            mocker.call('cluster', '2|test', 'all'),
            mocker.call('cluster', '3|test', 'all')
        ])

    def test_queryIdens_no_matching_ids_found(self, testInstance, mocker):
        mockRedisCheck = mocker.patch.object(ClusterProcess, 'checkSetRedis')
        mockRedisCheck.side_effect = [False, True, False]

        mockGetBatch = mocker.patch.object(ClusterProcess, 'getRecordBatches')
        mockGetBatch.side_effect = [[(1, ['4|lcc', '5|oclc'])], [(2, ['6|ddc'])], []]

        testIDs = testInstance.queryIdens(['1|oclc', '2|oclc', '3|oclc'])

        assert testIDs == [1, 2]
        mockRedisCheck.assert_has_calls([
            mocker.call('cluster', '1|oclc', 'all'),
            mocker.call('cluster', '2|oclc', 'all'),
            mocker.call('cluster', '3|oclc', 'all')
        ])
        assert set(mockGetBatch.call_args_list[0][0][0]) == set(['1|oclc', '3|oclc'])
        assert mockGetBatch.call_args_list[0][0][1] == set([])
        assert set(mockGetBatch.call_args_list[1][0][0]) == set(['5|oclc'])
        assert mockGetBatch.call_args_list[1][0][1] == set([1])
        assert set(mockGetBatch.call_args_list[2][0][0]) == set([])
        assert mockGetBatch.call_args_list[2][0][1] == set([1, 2])

    def test_getRecordBatches(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.session.query().filter().filter().all.side_effect = [[1], [2, 3]]

        testMatches = testInstance.getRecordBatches([str(i) for i in range(103)], set([]))

        assert testMatches == [1, 2, 3]
        testInstance.session.query().filter.call_args[0][0].compare(~Record.id.in_([]))

        testIDArray = '{{{}}}'.format(','.join([str(i) for i in range(100)]))
        testInstance.session.query().filter().filter.call_args[0][0].compare(Record.identifiers.overlap(testIDArray))

    def test_indexWorkInElasticSearch(self, testInstance, mocker):
        mockElasticInst = mocker.patch('processes.sfrCluster.SFRElasticRecordManager')
        mockESManager = mocker.MagicMock()
        mockElasticInst.return_value = mockESManager

        testInstance.indexWorkInElasticSearch('testDBWork')

        mockElasticInst.assert_called_once_with('testDBWork')
        mockESManager.getCReateWork.assert_called_once
        mockESManager.saveWork.assert_called_once
