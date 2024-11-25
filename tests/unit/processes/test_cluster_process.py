from sqlalchemy.exc import DataError
from processes.cluster import ClusterError
import pytest

from tests.helper import TestHelpers
from processes.cluster import ClusterProcess, ClusterError
from model import Record


class TestClusterProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestClusterProcess(ClusterProcess):
            def __init__(self):
                self.records = []
                self.db_manager = mocker.MagicMock()
                self.constants = { 'iso639': {} }
                self.session = mocker.Mock()
                self.engine = mocker.Mock()
        
        return TestClusterProcess()

    @pytest.fixture
    def testRecord(self, mocker):
        return mocker.MagicMock(id=1, title='Test', identifiers=['2|oclc'], uuid='testUUID')

    def test_runProcess_daily(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'cluster_records')

        testInstance.process = 'daily'
        testInstance.runProcess()

        mockCluster.assert_called_once

    def test_runProcess_complete(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'cluster_records')

        testInstance.process = 'complete'
        testInstance.runProcess()

        mockCluster.assert_called_once_with(full=True)

    def test_runProcess_custom(self, testInstance, mocker):
        mockCluster = mocker.patch.object(ClusterProcess, 'cluster_records')

        testInstance.process = 'custom'
        testInstance.ingestPeriod = 'testDate'
        testInstance.runProcess()

        mockCluster.assert_called_once_with(start_datetime='testDate')

    def test_cluster_records_not_full(self, testInstance, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            cluster_record=mocker.DEFAULT,
            update_elastic_search=mocker.DEFAULT,
            delete_stale_works=mocker.DEFAULT,
        )

        mockQuery = mocker.MagicMock()

        testInstance.db_manager.session.query().filter().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.first.side_effect = ['rec1', 'rec2', None]

        clusterMocks['cluster_record'].side_effect = [
            ('work1', ['uuid2', 'uuid3']), ('work4', ['uuid3', 'uuid4'])
        ]

        testInstance.cluster_records()

        assert mockQuery.first.call_count == 3

        clusterMocks['cluster_record'].assert_has_calls([mocker.call('rec1'), mocker.call('rec2')])
        clusterMocks['update_elastic_search'].assert_called_once_with(
            ['work1', 'work4'], set(['uuid2', 'uuid3', 'uuid4'])
        )
        clusterMocks['delete_stale_works'].assert_called_once_with(
            set(['uuid2', 'uuid3', 'uuid4'])
        )
        testInstance.db_manager.session.commit.assert_called_once()

    def test_cluster_records_custom_range(self, testInstance, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            cluster_record=mocker.DEFAULT,
            update_elastic_search=mocker.DEFAULT,
            delete_stale_works=mocker.DEFAULT,
        )
        mockQuery = mocker.MagicMock()
        testInstance.process = 'custom'
        mocker.patch('processes.cluster.datetime')

        testInstance.db_manager.session.query().filter().filter.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.first.side_effect = ['rec{}'.format(i) for i in range(50)] + [None]

        clusterMocks['cluster_record'].side_effect = [
            ('work{}'.format(i), []) for i in range(50)
        ]

        testInstance.cluster_records(start_datetime='testDate')

        assert mockQuery.first.call_count == 51
        clusterMocks['cluster_record'].assert_has_calls(
            [mocker.call('rec{}'.format(i)) for i in range(50)]
        )
        clusterMocks['update_elastic_search'].assert_has_calls([
            mocker.call(['work{}'.format(i) for i in range(50)], set([])),
            mocker.call([], set([]))
        ])
        clusterMocks['delete_stale_works'].assert_has_calls([
            mocker.call(set([])), mocker.call(set([]))
        ])

    def test_cluster_records_full(self, testInstance, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            cluster_record=mocker.DEFAULT,
            update_elastic_search=mocker.DEFAULT,
            delete_stale_works=mocker.DEFAULT,
            update_cluster_status=mocker.DEFAULT
        )

        mockQuery = mocker.MagicMock()

        testInstance.db_manager.session.query().filter().filter().filter().filter().filter.return_value = mockQuery
        mockQueryResponses = [mocker.MagicMock(id=1), mocker.MagicMock(id=2), None]
        mockQuery.first.side_effect = mockQueryResponses

        clusterMocks['cluster_record'].side_effect = [('work1', []), ClusterError]

        testInstance.cluster_records(full=True)

        assert mockQuery.first.call_count == 3
        clusterMocks['update_cluster_status'].assert_called_once_with([2])

    def test_cluster_record_w_matching_records(self, testInstance, testRecord, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            find_all_matching_records=mocker.DEFAULT,
            cluster_matched_records=mocker.DEFAULT,
            create_work_from_editions=mocker.DEFAULT,
            update_cluster_status=mocker.DEFAULT
        )
        clusterMocks['find_all_matching_records'].return_value = ['3|test']
        clusterMocks['cluster_matched_records'].return_value = (['ed1', 'ed2'], ['inst1', 'inst2', 'inst3'])
        clusterMocks['create_work_from_editions'].return_value = ('testDBWork', ['uuid1', 'uuid2'])

        testWork, testDeleted = testInstance.cluster_record(testRecord)

        assert testWork == 'testDBWork'
        assert testDeleted == ['uuid1', 'uuid2']

        clusterMocks['find_all_matching_records'].assert_called_once_with(testRecord)
        clusterMocks['cluster_matched_records'].assert_called_once_with(['3|test', 1])
        clusterMocks['create_work_from_editions'].assert_called_once_with(
            ['ed1', 'ed2'], ['inst1', 'inst2', 'inst3']
        )
        testInstance.db_manager.session.flush.assert_called_once()
        clusterMocks['update_cluster_status'].assert_called_once_with(['3|test', 1])

    def test_cluster_record_wo_matching_records(self, testInstance, testRecord, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            find_all_matching_records=mocker.DEFAULT,
            cluster_matched_records=mocker.DEFAULT,
            create_work_from_editions=mocker.DEFAULT,
            update_cluster_status=mocker.DEFAULT
        )
        clusterMocks['find_all_matching_records'].return_value = []
        clusterMocks['cluster_matched_records'].return_value = (['ed1'], ['inst1'])
        clusterMocks['create_work_from_editions'].return_value = ('testDBWork', ['uuid1', 'uuid2'])

        testWork, testDeleted = testInstance.cluster_record(testRecord)

        assert testWork == 'testDBWork'
        assert testDeleted == ['uuid1', 'uuid2']

        clusterMocks['find_all_matching_records'].assert_called_once_with(testRecord)
        clusterMocks['cluster_matched_records'].assert_called_once_with([1])
        clusterMocks['create_work_from_editions'].assert_called_once_with(['ed1'], ['inst1'])
        testInstance.db_manager.session.flush.assert_called_once()
        clusterMocks['update_cluster_status'].assert_called_once_with([1])

    def test_cluster_record_error(self, testInstance, testRecord, mocker):
        clusterMocks = mocker.patch.multiple(
            ClusterProcess,
            tokenize_title=mocker.DEFAULT,
            find_all_matching_records=mocker.DEFAULT,
            cluster_matched_records=mocker.DEFAULT,
            create_work_from_editions=mocker.DEFAULT,
            update_cluster_status=mocker.DEFAULT
        )

        clusterMocks['find_all_matching_records'].return_value = []
        clusterMocks['cluster_matched_records'].return_value = (['ed1'], ['inst1'])
        clusterMocks['create_work_from_editions'].return_value = ('testDBWork', ['uuid1', 'uuid2'])
        clusterMocks['tokenize_title'].return_value = set(['test', 'title'])

        testWork, testDeleted = testInstance.cluster_record(testRecord)

        testInstance.db_manager.session.flush.side_effect = DataError('test', {}, 'testing')

        with pytest.raises(ClusterError):
            testInstance.cluster_record(testRecord)

    def test_update_cluster_status(self, testInstance):
        testInstance.update_cluster_status([1])

        testInstance.db_manager.session.query().filter().update.assert_called_once()

    def test_cluster_matched_records(self, testInstance, mocker):
        mockMLModel = mocker.MagicMock()
        mockMLModel.parseEditions.return_value = ['ed1', 'ed2']
        mockKManager = mocker.patch('processes.cluster.KMeansManager')
        mockKManager.return_value = mockMLModel

        testInstance.db_manager.session.query().filter().all.return_value = ['rec1', 'rec2', 'rec3']
        testEditions, testRecords = testInstance.cluster_matched_records([1, 2, 3]) 

        assert testEditions == ['ed1', 'ed2']
        assert testRecords == ['rec1', 'rec2', 'rec3']

        testInstance.db_manager.session.query.filter.all.assert_called_once
        mockKManager.assert_called_once_with(['rec1', 'rec2', 'rec3'])
        mockMLModel.createDF.assert_called_once
        mockMLModel.generateClusters.assert_called_once
        mockMLModel.parseEditions.assert_called_once

    def test_create_work_from_editions(self, testInstance, mocker):
        mockRecManager = mocker.MagicMock()
        mockRecManager.buildWork.return_value = 'testWorkData'
        mockRecManager.work = 'testWork'
        mockRecManager.mergeRecords.return_value = ['uuid1', 'uuid2']
        mockManagerInst = mocker.patch('processes.cluster.SFRRecordManager')
        mockManagerInst.return_value = mockRecManager

        testWork = testInstance.create_work_from_editions('testEditions', 'testInstances')

        assert testWork == ('testWork', ['uuid1', 'uuid2'])
        mockManagerInst.assert_called_once_with(testInstance.db_manager.session, {})
        mockRecManager.buildWork.assert_called_once_with('testInstances', 'testEditions')
        mockRecManager.saveWork.assert_called_once_with('testWorkData')
        mockRecManager.mergeRecords.assert_called_once()

    def test_find_all_matching_records_success(self, testInstance, testRecord, mocker):
        mockGetBatches = mocker.patch.object(ClusterProcess, 'get_matched_records')
        mockGetBatches.side_effect = [
            [('title1', 1, ['1|isbn']), ('title2', 2, ['2|oclc', '3|other'])],
            [('title3', 3, ['4|oclc'])],
            [('title4', 4, ['5|oclc'])],
            []
        ]

        mockCompareTitles = mocker.patch.object(ClusterProcess, 'titles_overlap')
        mockCompareTitles.return_value = False

        testIDs = testInstance.find_all_matching_records(testRecord)

        assert testIDs == [1, 2]
        assert mockGetBatches.call_count == 4

    def test_find_all_matching_records_exceed_cluster_threshold(self, testInstance, testRecord, mocker):
        mockGetBatch = mocker.patch.object(ClusterProcess, 'get_matched_records')
        mockGetBatch.side_effect = [
            [('title{}'.format(i), i, ['{}|test'.format(i)]) for i in range(10001)],
            []
        ]

        with pytest.raises(Exception):
            testInstance.find_all_matching_records(testRecord)

    def test_get_matched_records(self, testInstance, mocker):
        mockFormatArray = mocker.patch.object(ClusterProcess, 'format_identifiers')
        mockFormatArray.return_value = 'testIdentifierArray'

        testInstance.db_manager.session.query().filter().filter().filter().all.side_effect = [[1], [2, 3]]

        testMatches = testInstance.get_matched_records([str(i) for i in range(103)], set([]))

        assert testMatches == [1, 2, 3]
        testInstance.db_manager.session.query().filter.call_args[0][0].compare(~Record.id.in_([]))
        testInstance.db_manager.session.query().filter().filter.call_args[0][0].compare(Record.identifiers.overlap('testIdentifierArray'))

    def test_format_identifiers(self, testInstance):
        assert testInstance.format_identifiers(['{test}|test', 'multi,test|test'])\
            == '{"{test}|test","multi,test|test"}'

    def test_tokenize_title_success(self, testInstance):
        assert testInstance.tokenize_title('A Test Title') == set(['test', 'title'])

    def test_tokenize_title_error(self, testInstance):
        with pytest.raises(ClusterError):
            testInstance.tokenize_title(None)
