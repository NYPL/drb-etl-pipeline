import pytest

from api.db import DBClient
from api.utils import APIUtils
from model import Work, Edition, Item, Link, Rights, Identifier
from model.postgres.item import ITEM_LINKS


class TestDBClient:
    @pytest.fixture
    def testInstance(self, mocker):
        class MockDBClient(DBClient):
            def __init__(self, engine):
                self.engine = mocker.MagicMock()

        return MockDBClient('testEngine')

    def test_fetchSearchedWorks(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().join().join().filter().all.return_value = ['work1', 'work3']

        mockFlatten = mocker.patch.object(APIUtils, 'flatten')
        mockFlatten.return_value = [1, 2, 3]

        workResult = testInstance.fetchSearchedWorks(
            [('uuid1', 'ed1'), ('uuid2', 'ed2'), ('uuid3', 'ed3')]
        )

        assert workResult == ['work1', 'work3']
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once
        mockSession.query.join.outerjoin.filter.all.assert_called_once

    def test_fetchSingleWork(self, testInstance, mocker):
        mockCreator = mocker.MagicMock()
        mockMaker = mocker.patch('api.db.sessionmaker')
        mockMaker.return_value = mockCreator
        mockSession = mocker.MagicMock()
        mockCreator.return_value = mockSession
        mockSession.query().join().join().filter().first.return_value = 'testWork'

        workResult = testInstance.fetchSingleWork('uuid')

        assert workResult == 'testWork'
        mockMaker.assert_called_once_with(bind=testInstance.engine)
        mockCreator.assert_called_once
        mockSession.query.join.outerjoin.filter.first.assert_called_once
