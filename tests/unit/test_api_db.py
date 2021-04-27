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
                self.session = mocker.MagicMock()

        return MockDBClient('testEngine')

    @pytest.fixture
    def testCountQuery(self):
        return text("""SELECT relname AS table, reltuples AS row_count
            FROM pg_class c JOIN pg_namespace n ON (n.oid = c.relnamespace)
            WHERE nspname NOT IN ('pg_catalog', 'information_schema')
            AND relkind = 'r'
            AND relname IN ('records', 'works', 'editions', 'items', 'links')
        """)

    def test_createSession(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession

        testInstance.createSession()

        assert testInstance.session == mockSession
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once()

    def test_closeSession(self, testInstance):
        testInstance.closeSession()

        testInstance.session.close.assert_called_once()

    def test_fetchSearchedWorks(self, testInstance, mocker):
        testInstance.session.query().join().options().filter().all.return_value = ['work1', 'work3']

        mockFlatten = mocker.patch.object(APIUtils, 'flatten')
        mockFlatten.return_value = [1, 2, 3]

        workResult = testInstance.fetchSearchedWorks(
            [('uuid1', 'ed1'), ('uuid2', 'ed2'), ('uuid3', 'ed3')]
        )

        assert workResult == ['work1', 'work3']
        testInstance.session.query().join().options().filter().all.assert_called_once()

    def test_fetchSingleWork(self, testInstance, mocker):
        testInstance.session.query().options().filter().first.return_value = 'testWork'

        workResult = testInstance.fetchSingleWork('uuid')

        assert workResult == 'testWork'
        testInstance.session.query().options().filter().first.assert_called_once()

    def test_fetchSingleEdition(self, testInstance, mocker):
        testInstance.session.query().options().filter().first.return_value = 'testEdition'

        editionResult = testInstance.fetchSingleEdition('editionID')

        assert editionResult == 'testEdition'
        testInstance.session.query().options().filter().first.assert_called_once()

    def test_fetchSingleLink(self, testInstance, mocker):
        testInstance.session.query().filter().first.return_value = 'testLink'

        editionResult = testInstance.fetchSingleLink('linkID')

        assert editionResult == 'testLink'
        testInstance.session.query().filter().first.assert_called_once()

    def test_fetchRecordsByUUID(self, testInstance, mocker):
        testInstance.session.query().filter().all.return_value = 'testRecords'

        editionResult = testInstance.fetchRecordsByUUID(['uuid1', 'uuid2'])

        assert editionResult == 'testRecords'
        testInstance.session.query().filter().all.assert_called_once()

    def test_fetchRowCounts(self, testInstance, testCountQuery, mocker):
        testInstance.session.execute.return_value = 'testCounts'

        totalResult = testInstance.fetchRowCounts()

        assert totalResult == 'testCounts'
        testInstance.session.execute.call_args[0][0].compare(testCountQuery)
