from flask import Flask
import pytest

from api.blueprints.drbS3 import validateToken, s3ObjectLinkFetch
from api.utils import APIUtils

from werkzeug.datastructures import ImmutableMultiDict 

class TestS3Blueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT,
            generate_presigned_url=mocker.DEFAULT,
            validatePassword=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp
    
    def test_s3ObjectLinkFetch_success(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'
        mockUtils['generate_presigned_url'].return_value = 'https://digital-research-books-beta.nypl.org/work/2263dbf4-51c2-4f6e-b9eb-e1def96b48d4?featured=9401263'

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbS3.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbS3.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context('/?key=manifests/met/10935.json', headers={'Authorization': 'Basic testAuth'}):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qa')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 's3ObjectLinkFetch', {'message': 'https://digital-research-books-beta.nypl.org/work/2263dbf4-51c2-4f6e-b9eb-e1def96b48d4?featured=9401263'}
            )

    def test_s3ObjectLinkFetch_fail(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'
        mockUtils['generate_presigned_url'].return_value = 'https://drb-files-qaFail.s3.amazonaws.com/manifests/met/10935.json?'

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbS3.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbS3.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True
    
        with testApp.test_request_context('/?key=manifests/met/10935.json', headers={'Authorization': 'Basic testAuth'}):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qaFail')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(404, 's3ObjectLinkFetch', {'Bucket/Key does not exist': 'https://drb-files-qaFail.s3.amazonaws.com/manifests/met/10935.json?'})

    def test_validateToken_success(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbS3.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbS3.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Basic testAuth'}
        ):
            decoratedFunction()

            mockBase64.assert_called_once_with(b'testAuth')

            mockFunc.assert_called_once_with(user='testUser')

    def test_validateToken_error_no_header(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context('/'):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                403, 'authResponse',
                {'message': 'user/password not provided'}
            )

    def test_validateToken_error_auth(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbS3.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbS3.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = False

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Basic testAuth'}
        ):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                401, 'authResponse',
                {'message': 'invalid user/password'}
            )