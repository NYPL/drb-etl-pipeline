from flask import Flask
import pytest

from api.blueprints.drbUtils import languageCounts, totalCounts
from api.utils import APIUtils

class TestEditionBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT,
            formatLanguages=mocker.DEFAULT,
            formatTotals=mocker.DEFAULT
        )
    
    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

    def test_languageCounts(self, mockUtils, testApp, mocker):
        mockES = mocker.MagicMock()
        mockESClient = mocker.patch('api.blueprints.drbUtils.ElasticClient')
        mockESClient.return_value = mockES

        mockUtils['normalizeQueryParams'].return_value = {'totals': ['true']}
        
        mockES.languageQuery.return_value = mocker.MagicMock(aggregations=['lang1', 'lang2'])

        mockUtils['formatLanguages'].return_value = 'testLanguageList'
        mockUtils['formatResponseObject'].return_value = 'languageListResponse'

        with testApp.test_request_context('/?totals=true'):
            testAPIResponse = languageCounts()

            assert testAPIResponse == 'languageListResponse'
            mockESClient.assert_called_once()

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockES.languageQuery.assert_called_once_with(True)
            mockUtils['formatLanguages'].assert_called_once_with(['lang1', 'lang2'], True)
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'languageCounts', 'testLanguageList'
            )

    def test_totalCounts(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbUtils.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchRowCounts.return_value = 'testTotalResult'

        mockUtils['formatTotals'].return_value = 'testTotalSummary'
        mockUtils['formatResponseObject'].return_value = 'totalsResponse'

        with testApp.test_request_context('/'):
            testAPIResponse = totalCounts()

            assert testAPIResponse == 'totalsResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockDB.fetchRowCounts.assert_called_once()
            mockUtils['formatTotals'].assert_called_once_with('testTotalResult')
            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'totalCounts', 'testTotalSummary'
            )
