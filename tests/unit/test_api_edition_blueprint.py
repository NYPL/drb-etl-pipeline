from flask import Flask
import pytest

from api.blueprints.drbEdition import editionFetch
from api.utils import APIUtils


class TestEditionBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            extractParamPairs=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT,
            formatEditionOutput=mocker.DEFAULT
        )
    
    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['READER_VERSION'] = 'test'

        return flaskApp

    def test_editionFetch_success_noFormat(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbEdition.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['true']}

        mockEdition = mocker.MagicMock(dcdw_uuids='testUUID')

        mockDB.fetchSingleEdition.return_value = mockEdition
        mockDB.fetchRecordsByUUID.return_value = 'testRecords'

        mockUtils['formatEditionOutput'].return_value = 'testEdition'
        mockUtils['formatResponseObject'].return_value\
            = 'singleEditionResponse'

        with testApp.test_request_context('/'):
            testAPIResponse = editionFetch(1)

            assert testAPIResponse == 'singleEditionResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatEditionOutput'].assert_called_once_with(
                mockEdition, records='testRecords', showAll=True, formats=[], reader='test'
            )
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleEdition', 'testEdition'
            )

    def test_editionFetch_success_format(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbEdition.DBClient')
        mockDBClient.return_value = mockDB

        queryParams = {'showAll': ['true']}
        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['true']}

        mockEdition = mocker.MagicMock(dcdw_uuids='testUUID')

        mockUtils['extractParamPairs'].side_effect = [
            [('format', 'requestable')]
        ]

        mockDB.fetchSingleEdition.return_value = mockEdition
        mockDB.fetchRecordsByUUID.return_value = 'testRecords'

        mockUtils['formatEditionOutput'].return_value = 'testEdition'
        mockUtils['formatResponseObject'].return_value\
            = 'singleEditionResponse'

        with testApp.test_request_context('/'):
            testAPIResponse = editionFetch(1)

            assert testAPIResponse == 'singleEditionResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['extractParamPairs'].assert_has_calls([
                mocker.call('filter', queryParams)
            ])
            mockUtils['formatEditionOutput'].assert_called_once_with(
                mockEdition, records='testRecords', showAll=True, 
                                    formats=['application/html+edd', 'application/x.html+edd'], reader='test'
            )
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'singleEdition', 'testEdition'
            )



    def test_editionFetch_missing(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbEdition.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['normalizeQueryParams'].return_value = {'showAll': ['true']}
        
        mockDB.fetchSingleEdition.return_value = None

        mockUtils['formatResponseObject'].return_value = '404Response'

        with testApp.test_request_context('/'):
            testAPIResponse = editionFetch(1)

            assert testAPIResponse == '404Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatEditionOutput'].assert_not_called()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'singleEdition',
                {'message': 'Unable to locate edition with id 1'}
            )
