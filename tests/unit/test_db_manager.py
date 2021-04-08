import pytest
from sqlalchemy.exc import OperationalError

from managers import DBManager


class TestDBManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mockDecrypt = mocker.patch.object(DBManager, 'decryptEnvVar')
        mockDecrypt.side_effect = ['user', 'pswd', 'host', 'port', 'name']

        return DBManager()

    def test_initializer(self, testInstance):
        assert testInstance.user == 'user'
        assert testInstance.pswd == 'pswd'
        assert testInstance.host == 'host'
        assert testInstance.port == 'port'
        assert testInstance.db == 'name'
        assert testInstance.engine == None
        assert testInstance.session == None

    def test_generateEngine_success(self, testInstance, mocker):
        mockCreate = mocker.patch('managers.db.create_engine')
        mockCreate.return_value = 'testEngine'

        testInstance.generateEngine()

        assert testInstance.engine == 'testEngine'
        mockCreate.assert_called_once_with(
            'postgresql://user:pswd@host:port/name'
        )

    def test_generateEngine_error(self, testInstance, mocker):
        mockCreate = mocker.patch('managers.db.create_engine')
        mockCreate.side_effect = Exception

        with pytest.raises(Exception):
            testInstance.generateEngine()

    def test_initializeDatabase_run(self, testInstance, mocker):
        testInstance.engine = mocker.MagicMock()
        testInstance.engine.dialect.has_table.return_value = None
        mockBase = mocker.patch('managers.db.Base')

        testInstance.initializeDatabase()

        testInstance.engine.dialect.has_table.assert_called_once_with(
            testInstance.engine, 'works'
        )
        mockBase.metadata.create_all.assert_called_once_with(testInstance.engine)

    def test_initializeDatabase_skip(self, testInstance, mocker):
        testInstance.engine = mocker.MagicMock()
        testInstance.engine.dialect.has_table.return_value = 'testTable'
        mockBase = mocker.patch('managers.db.Base')

        testInstance.initializeDatabase()

        testInstance.engine.dialect.has_table.assert_called_once_with(
            testInstance.engine, 'works'
        )
        mockBase.metadata.create_all.assert_not_called

    def test_createSession_engine_exists(self, testInstance, mocker):
        mockSessionmaker = mocker.patch('managers.db.sessionmaker')
        mockSessionManager = mocker.MagicMock()
        mockSessionmaker.return_value = mockSessionManager
        mockSessionManager.return_value = 'testSession'
        testInstance.engine = 'testEngine'

        testInstance.createSession()

        assert testInstance.session == 'testSession'
        mockSessionmaker.assert_called_once_with(bind='testEngine', autoflush=False)
        mockSessionManager.assert_called_once

    def test_createSession_engine_not_exists_autoflush(self, testInstance, mocker):
        mockSessionmaker = mocker.patch('managers.db.sessionmaker')
        mockSessionManager = mocker.MagicMock()
        mockSessionmaker.return_value = mockSessionManager
        mockSessionManager.return_value = 'testSession'
        testInstance.engine = None

        mockGenerate = mocker.patch.object(DBManager, 'generateEngine')

        testInstance.createSession(autoflush=True)

        assert testInstance.session == 'testSession'
        mockGenerate.assert_called_once
        mockSessionmaker.assert_called_once_with(bind=None, autoflush=True)

    def test_startSession(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.startSession()

        testInstance.session.begin_nested.assert_called_once

    def test_commitChanges_success(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.commitChanges()

        testInstance.session.commit.assert_called_once()

    def test_commitChanges_deadlock(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()
        testInstance.session.commit.side_effect = [
            OperationalError('test', 'test', 'test'), None
        ]

        mockRollback = mocker.patch.object(DBManager, 'rollbackChanges')

        testInstance.commitChanges()

        assert testInstance.session.commit.call_count == 2
        mockRollback.assert_called_once()

    def test_commitChanges_deadlock_repeated(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()
        testInstance.session.commit.side_effect = OperationalError('test', 'test', 'test')

        mockRollback = mocker.patch.object(DBManager, 'rollbackChanges')

        testInstance.commitChanges()

        assert testInstance.session.commit.call_count == 2
        assert mockRollback.call_count == 2

    def test_rollbackChanges(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.rollbackChanges()

        testInstance.session.rollback.assert_called_once

    def test_closeConnection(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()
        testInstance.engine = mocker.MagicMock()
        mockCommit = mocker.patch.object(DBManager, 'commitChanges')

        testInstance.closeConnection()

        mockCommit.assert_called_once
        testInstance.session.close.assert_called_once
        testInstance.engine.dispose.assert_called_once

    def test_bulkSaveObjects_default(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.bulkSaveObjects([1, 2, 3])

        testInstance.session.bulk_save_objects.assert_called_once_with(
            [1, 2, 3], update_changed_only=True
        )
        testInstance.session.commit.assert_called_once()
        testInstance.session.flush.assert_called_once()

    def test_bulkSaveObjects_onlyChanged_false(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()

        testInstance.bulkSaveObjects([1, 2, 3], onlyChanged=False)

        testInstance.session.bulk_save_objects.assert_called_once_with(
            [1, 2, 3], update_changed_only=False
        )

    def test_bulkSaveObjects_readlock_retry(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()
        testInstance.session.bulk_save_objects.side_effect = [
            OperationalError('test', 'test', 'test'), None
        ]

        mockRollback = mocker.patch.object(DBManager, 'rollbackChanges')

        testInstance.bulkSaveObjects([1, 2, 3])

        testInstance.session.bulk_save_objects.assert_has_calls([
            mocker.call([1, 2, 3], update_changed_only=True),
            mocker.call([1, 2, 3], update_changed_only=True)
        ])
        mockRollback.assert_called_once()

    def test_bulkSaveObjects_readlock_retry_fail(self, testInstance, mocker):
        testInstance.session = mocker.MagicMock()
        testInstance.session.bulk_save_objects.side_effect = OperationalError('test', 'test', 'test')

        mockRollback = mocker.patch.object(DBManager, 'rollbackChanges')

        testInstance.bulkSaveObjects([1, 2, 3], onlyChanged=False)

        testInstance.session.bulk_save_objects.assert_has_calls([
            mocker.call([1, 2, 3], update_changed_only=False),
            mocker.call([1, 2, 3], update_changed_only=False)
        ])
        assert mockRollback.call_count == 2

    def test_decryptEnvVar_present(self, mocker):
        mocker.patch.dict('os.environ', {'test': 'testValue'})

        decryptedVar = DBManager.decryptEnvVar('test')

        assert decryptedVar == 'testValue'

    def test_decryptEnvVar_missing(self, mocker):
        mocker.patch.dict('os.environ', {'test': 'testValue'})

        decryptedVar = DBManager.decryptEnvVar('other')

        assert decryptedVar == None
