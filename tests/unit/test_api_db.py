import pytest
from sqlalchemy.sql import text

from api.db import DBClient
from api.utils import APIUtils


class TestDBClient:
    @pytest.fixture
    def testInstance(self, mocker):
        class MockDBClient(DBClient):
            def __init__(self, engine):
                self.engine = mocker.MagicMock()

        return MockDBClient('testEngine')

    @pytest.fixture
    def testCountQuery(self):
        return text("""SELECT relname AS table, reltuples AS row_count
            FROM pg_class c JOIN pg_namespace n ON (n.oid = c.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND relkind = 'r'
            AND relname IN ('records', 'works', 'editions', 'items', 'links')
        """)

    def test_fetchSearchedWorks(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().join().options().join().options().filter()\
            .all.return_value = ['work1', 'work3']

        mockFlatten = mocker.patch.object(APIUtils, 'flatten')
        mockFlatten.return_value = [1, 2, 3]

        workResult = testInstance.fetchSearchedWorks(
            [('uuid1', 'ed1'), ('uuid2', 'ed2'), ('uuid3', 'ed3')]
        )

        assert workResult == ['work1', 'work3']
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.query().join().options().join().options().filter()\
            .all.assert_called_once()

    def test_fetchSingleWork(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().filter().first.return_value = 'testWork'

        workResult = testInstance.fetchSingleWork('uuid')

        assert workResult == 'testWork'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.query().filter().first.assert_called_once()

    def test_fetchSingleEdition(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().filter().first.return_value = 'testEdition'

        editionResult = testInstance.fetchSingleEdition('editionID')

        assert editionResult == 'testEdition'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.query().filter().first.assert_called_once()

    def test_fetchSingleLink(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().filter().first.return_value = 'testLink'

        editionResult = testInstance.fetchSingleLink('linkID')

        assert editionResult == 'testLink'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.query().filter().first.assert_called_once()

    def test_fetchRecordsByUUID(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().filter().all.return_value = 'testRecords'

        editionResult = testInstance.fetchRecordsByUUID(['uuid1', 'uuid2'])

        assert editionResult == 'testRecords'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.query().filter().all.assert_called_once()

    def test_fetchRowCounts(self, testInstance, testCountQuery, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession

        mockSession.execute.return_value = 'testCounts'

        totalResult = testInstance.fetchRowCounts()

        assert totalResult == 'testCounts'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()
        mockSession.execute.call_args[0][0].compare(testCountQuery)
