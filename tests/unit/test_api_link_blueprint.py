from flask import Flask, request
import pytest

from api.blueprints.drbLink import linkFetch
from api.utils import APIUtils

class TestLinkBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            formatLinkOutput=mocker.DEFAULT
        )
    
    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

    def test_linkFetch_success(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbLink.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchSingleLink.return_value = 'dbLinkRecord'

        mockUtils['formatLinkOutput'].return_value = 'testLink'
        mockUtils['formatResponseObject'].return_value = 'singleLinkResponse'

        with testApp.test_request_context('/'):
            testAPIResponse = linkFetch(1)

            assert testAPIResponse == 'singleLinkResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['formatLinkOutput'].assert_called_once_with('dbLinkRecord', request=request)
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleLink', 'testLink'
            )

    def test_editionFetch_missing(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbLink.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchSingleLink.return_value = None

        mockUtils['formatResponseObject'].return_value = '404Response'

        with testApp.test_request_context('/'):
            testAPIResponse = linkFetch(1)

            assert testAPIResponse == '404Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['formatLinkOutput'].assert_not_called()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404, 'singleLink', {'message': 'Unable to locate link #1'}
            )
