from flask import Flask
import pytest

from api.blueprints.drbWork import workFetch
from api.utils import APIUtils


class TestSearchBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            extractParamPairs=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT,
            formatWorkOutput=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['READER_VERSION'] = 'test'

        return flaskApp

    def test_workFetch_success_showAll_true(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbWork.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['true']}

        mockDB.fetchSingleWork.return_value = 'dbWorkRecord'

        mockUtils['formatWorkOutput'].return_value = 'testWork'
        mockUtils['formatResponseObject'].return_value = 'singleWorkResponse'

        with testApp.test_request_context('/?showAll=true'):
            testAPIResponse = workFetch('testUUID')

            assert testAPIResponse == 'singleWorkResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once
            mockUtils['formatWorkOutput'].assert_called_once_with(
                'dbWorkRecord', None, showAll=True, dbClient=mockDB, formats=[], reader='test'
            )
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleWork', 'testWork'
            )

    def test_workFetch_success_format(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbWork.DBClient')
        mockDBClient.return_value = mockDB

        queryParams = {'showAll': ['true']}
        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['true']}

        mockUtils['extractParamPairs'].side_effect = [
            [('format', 'requestable')]
        ]

        mockDB.fetchSingleWork.return_value = 'dbWorkRecord'

        mockUtils['formatWorkOutput'].return_value = 'testWork'
        mockUtils['formatResponseObject'].return_value = 'singleWorkResponse'

        with testApp.test_request_context('/?showAll=true'):
            testAPIResponse = workFetch('testUUID')

            assert testAPIResponse == 'singleWorkResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once
            mockUtils['extractParamPairs'].assert_has_calls([
                mocker.call('filter', queryParams)
            ])
            mockUtils['formatWorkOutput'].assert_called_once_with(
                'dbWorkRecord', None, showAll=True, dbClient=mockDB, formats=['application/html+edd', 'application/x.html+edd'], reader='test'
            )
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleWork', 'testWork'
            )

    def test_workFetch_success_showAll_false(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbWork.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['false']}

        mockDB.fetchSingleWork.return_value = 'dbWorkRecord'

        mockUtils['formatWorkOutput'].return_value = 'testWork'
        mockUtils['formatResponseObject'].return_value = 'singleWorkResponse'

        with testApp.test_request_context('/?showAll=false'):
            testAPIResponse = workFetch('testUUID')

            assert testAPIResponse == 'singleWorkResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once
            mockUtils['formatWorkOutput'].assert_called_once_with(
                'dbWorkRecord', None, showAll=False, dbClient=mockDB, formats=[], reader='test'
            )
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleWork', 'testWork'
            )

    def test_workFetch_failure(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbWork.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['normalizeQueryParams'].return_value = {}

        mockDB.fetchSingleWork.return_value = None

        mockUtils['formatResponseObject'].return_value = 'errorResponse'

        with testApp.test_request_context('/testUUID?showAll=false'):
            testAPIResponse = workFetch('testUUID')

            assert testAPIResponse == 'errorResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatWorkOutput'].assert_not_called()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'singleWork',
                {'message': 'Unable to locate work with UUID testUUID'}
            )
