import pytest

from tests.helper import TestHelpers
from processes.core import CoreProcess


class TestCoreProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def coreInstance(self):
        return CoreProcess('TestProcess', 'testFile', 'testDate', 'testRecord')

    def test_coreProcess_initial_values(self, coreInstance):
        # Core properties set by this class
        assert coreInstance.process == 'TestProcess'
        assert coreInstance.customFile == 'testFile'
        assert coreInstance.ingestPeriod == 'testDate'
        assert coreInstance.singleRecord == 'testRecord'
        assert len(coreInstance.records) == 0

        # Properties set by the DBManager
        assert coreInstance.engine is None
        assert coreInstance.session is None
        assert coreInstance.user == 'test_psql_user'
        assert coreInstance.host == 'test_psql_host'
        assert coreInstance.pswd == 'test_psql_pswd'
        assert coreInstance.port == 'test_psql_port'
        assert coreInstance.db == 'test_psql_name'

    def test_addDCDWToUpdateList_existing(self, coreInstance, mocker):
        mockSession = mocker.MagicMock()
        mockSession.query().filter().first.return_value = 'existing_record'
        coreInstance.session = mockSession

        mockRecord = mocker.MagicMock()
        coreInstance.addDCDWToUpdateList(mockRecord)

        mockSession.assert_called_once
        mockRecord.updateExisting.assert_called_with('existing_record')
        assert list(coreInstance.records)[0] == 'existing_record'

    def test_addDCDWToUpdateList_new(self, coreInstance, mocker):
        mockSession = mocker.MagicMock()
        mockSession.query().filter().first.return_value = None
        coreInstance.session = mockSession

        mockRecord = mocker.MagicMock()
        mockDocument = mocker.MagicMock()
        mockRecord.record = mockDocument
        coreInstance.addDCDWToUpdateList(mockRecord)

        mockSession.assert_called_once
        assert list(coreInstance.records)[0] == mockDocument

    def test_addDCDWToUpdateList_new_save_records(self, coreInstance, mocker):
        coreInstance.records = set(['record{}'.format(i) for i in range(999)])

        mockSession = mocker.MagicMock()
        mockSession.query().filter().first.return_value = None
        coreInstance.session = mockSession

        mockSave = mocker.patch.object(CoreProcess, 'saveRecords')

        mockRecord = mocker.MagicMock()
        mockDocument = mocker.MagicMock()
        mockRecord.record = mockDocument
        coreInstance.addDCDWToUpdateList(mockRecord)

        mockSession.assert_called_once
        mockSave.assert_called_once
        assert len(coreInstance.records) == 0

    def test_saveRecords(self, coreInstance, mocker):
        mockBulkSave = mocker.patch.object(CoreProcess, 'bulkSaveObjects')
        coreInstance.records = ['record{}'.format(i) for i in range(3)]

        coreInstance.saveRecords()

        mockBulkSave.assert_called_with(['record0', 'record1', 'record2'])
    
    def test_windowedQuery_single(self, coreInstance, mocker):
        mockQuery = mocker.MagicMock(is_single_entity=True)
        mockQuery.add_column().order_by.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.limit().all.side_effect = [[('rec1', 1), ('rec2', 2), ('rec3', 3)], None]

        coreInstance.ingestLimit = None
        assert list(coreInstance.windowedQuery(mocker.MagicMock(id=1), mockQuery)) == ['rec1', 'rec2', 'rec3']

    def test_windowedQuery_tuple(self, coreInstance, mocker):
        mockQuery = mocker.MagicMock(is_single_entity=False)
        mockQuery.add_column().order_by.return_value = mockQuery
        mockQuery.filter.return_value = mockQuery
        mockQuery.limit().all.side_effect = [[('rec1', 1, 1), ('rec2', 2, 2), ('rec3', 3, 3)], None]

        coreInstance.ingestLimit = None
        assert list(coreInstance.windowedQuery(mocker.MagicMock(id=1), mockQuery)) == [('rec1',), ('rec2',), ('rec3',)]
