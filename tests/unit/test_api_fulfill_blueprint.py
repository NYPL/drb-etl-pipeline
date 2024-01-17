from flask import Flask
import pytest

import jwt

from api.blueprints.drbFulfill import itemFulfill
from api.utils import APIUtils
from model.postgres.link import Link


class TestSearchBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['READER_VERSION'] = 'test'

        return flaskApp

    @pytest.fixture
    def mockDB(self, mocker, monkeypatch):
        mockDB = mocker.MagicMock()
        mockDB.__enter__.return_value = mockDB
        mockDB.fetchSingleLink.return_value = Link(flags = {"nypl_login": True})
        mocker.patch('api.blueprints.drbFulfill.DBClient').return_value = mockDB

        monkeypatch.setenv('NYPL_API_CLIENT_PUBLIC_KEY', "SomeKeyValue")

    def test_itemFulfill_invalid_token(self, testApp, mockUtils, mockDB):
        with testApp.test_request_context('/fulfill/12345',
                                          headers={'Authorization': 'Bearer Whatever'}):
            itemFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'})

    def test_itemFulfill_no_bearer_auth(self, testApp, mockUtils, mockDB):
        with testApp.test_request_context('/fulfill/12345',
                                          headers={'Authorization': 'Whatever'}):
            itemFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'})

    def test_itemFulfill_empty_token(self, testApp, mockUtils, mockDB):
        with testApp.test_request_context('/fulfill/12345',
                                          headers={'Authorization': ''}):
            itemFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'})

    def test_itemFulfill_no_header(self, testApp, mockUtils, mockDB):
        with testApp.test_request_context('/fulfill/12345'):
            itemFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'})

    #def test_itemFulfill_valid(self, testApp, mockUtils, mockDB):
    #    with testApp.test_request_context('/fulfill/12345'):
    #        itemFulfill('12345')


