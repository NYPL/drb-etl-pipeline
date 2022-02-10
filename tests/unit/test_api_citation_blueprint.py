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

    #Test when work uuid and format values are set correctly
    def test_citationFetch_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
            mockDBClient.return_value = mockDB

            mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='A Title')
            
            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/?format=mla'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': 'A FORMATTED CITATION A Title'}
                )

    #Test for when the work uuid is not avaliable 
    def test_citationFetch_fail(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchSingleWork.return_value = None

        mockUtils['formatResponseObject'].return_value = '404Response'

        with testApp.test_request_context('testUUID/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == '404Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'citation',
                {'message': 'Unable to locate work with UUID testUUID'}
            )

    #Test for when request arguments for format are not set
    def test_citationFetch_fail2(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['formatResponseObject'].return_value = '400Response'

        with testApp.test_request_context('/?format='):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == '400Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatResponseObject'].assert_called_once_with(
                400,
                'pageNotFound',
                {'message': 'Need to specify citation format'}
            )