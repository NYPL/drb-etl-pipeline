from flask import Flask
import pytest

import jwt

from api.blueprints.drbFulfill import itemFulfill, fulfill
from api.utils import APIUtils
from model.postgres.link import Link


class TestSearchBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            getPresignedUrlFromObjectUrl="example.com/example.pdf"
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['READER_VERSION'] = 'test'
        flaskApp.register_blueprint(fulfill)

        return flaskApp

    @pytest.fixture
    def mockDB(self, mocker, monkeypatch):
        mockDB = mocker.MagicMock()
        mockDB.__enter__.return_value = mockDB
        mockDB.fetchSingleLink.return_value = Link(flags = {"nypl_login": True},
                            url="https://doc-example-bucket1.s3.us-west-2.amazonaws.com/puppy.png")
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

    def test_itemFulfill_invalid_iss(self, testApp, mockUtils, mockDB, mocker):
        with testApp.test_request_context('/fulfill/12345'):
            mocker.patch("jwt.decode", return_value={
                "iss": "https://example.com"
            })
            itemFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token', headers={'WWW-Authenticate': 'Bearer'})

    def test_itemFulfill_redirect(self, testApp, mockDB, mocker):
        mocker.patch("api.utils.APIUtils.getPresignedUrlFromObjectUrl", return_value="example.com/example.pdf")
        mocker.patch("jwt.decode", return_value={
            "iss": "https://www.nypl.org"
        })
        response = testApp.test_client().get(
            '/fulfill/12345',
            follow_redirects=False,
            headers={'Authorization': 'Bearer Whatever'}
        )
        assert response.status_code == 302
        assert response.location == "example.com/example.pdf"