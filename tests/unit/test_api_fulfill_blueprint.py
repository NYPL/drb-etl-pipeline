from flask import Flask
import pytest

import jwt

from api.blueprints.drbFulfill import workFulfill
from api.utils import APIUtils


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

    def test_workFulfill_invalid_token(self, testApp, mockUtils, monkeypatch):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': 'Bearer Whatever'}):
            monkeypatch.setenv('NYPL_API_CLIENT_PUBLIC_KEY', "SomeKeyValue")
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_no_bearer_auth(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': 'Whatever'}):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_empty_token(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': ''}):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_no_header(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345'):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')
        

    