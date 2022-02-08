from flask import Flask
import pytest

from api.blueprints.drbCitation import citationFetch
from api.utils import APIUtils


class TestCitationBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            normalizeQueryParams=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

    def test_citationFetch_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitations.DBClient')
            mockDBClient.return_value = mockDB

            mockDB.fetchSingleWork.return_value = 'dbWorkRecord'

            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': 'A FORMATTED CITATION'}
                )

    def test_citationFetch_fail(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbEdition.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchSingleWork.return_value = None

        mockUtils['formatResponseObject'].return_value = '404Response'

        with testApp.test_request_context('/'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == '404Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'citation',
                {'message': 'Unable to locate work with UUID testUUID'}
            )