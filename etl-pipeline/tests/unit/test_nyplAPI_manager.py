from oauthlib.oauth2 import TokenExpiredError
import pytest

from managers import NyplApiManager
from tests.helper import TestHelpers


class TestNYPLApiManager:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self):
        return NyplApiManager()

    def test_initializer(self, testInstance):
        assert testInstance.clientID == 'test_api_client'
        assert testInstance.clientSecret == 'test_api_secret'
        assert testInstance.tokenURL == 'test_api_token_url'
        assert testInstance.apiRoot == 'https://platform.nypl.org/api/v0.1'
        assert testInstance.token == None

    def test_generateAccessToken(self, testInstance, mocker):
        mockAppClient = mocker.patch('managers.nyplApi.BackendApplicationClient')
        mockAppClient.return_value = 'testClient'
        mockOauthSession = mocker.patch('managers.nyplApi.OAuth2Session')
        mockOauth = mocker.MagicMock(name='OauthInstance')
        mockOauth.fetch_token.return_value = 'testToken'
        mockOauthSession.return_value = mockOauth

        testInstance.generateAccessToken()

        assert testInstance.token == 'testToken'
        mockAppClient.assert_called_once_with('test_api_client')
        mockOauthSession.assert_called_once_with(client='testClient')
        mockOauth.fetch_token.assert_called_once_with(
            token_url='test_api_token_url',
            client_id='test_api_client',
            client_secret='test_api_secret'
        )

    def test_createClient(self, testInstance, mocker):
        mockOauthSession = mocker.patch('managers.nyplApi.OAuth2Session')
        mockOauthSession.return_value = 'testClient'
        
        testInstance.createClient()

        assert testInstance.client == 'testClient'
        mockOauthSession.assert_called_once_with('test_api_client', token=None)

    def test_queryApi(self, testInstance, mocker):
        mockClientCreate = mocker.patch.object(NyplApiManager, 'createClient')

        mockResp = mocker.MagicMock()
        mockResp.json.return_value = 'testAPIResponse'

        testInstance.client = mocker.MagicMock()
        testInstance.client.get.return_value = mockResp

        testResponse = testInstance.queryApi('test/path/request')

        assert testResponse == 'testAPIResponse'
        testInstance.client.get.assert_called_once_with(
            'https://platform.nypl.org/api/v0.1/test/path/request', timeout=15
        )
        mockClientCreate.assert_not_called

    def test_queyApi_tokenExpired(self, testInstance, mocker):
        mockRepeatClient = mocker.MagicMock()
        def resetClient():
            mockResp = mocker.MagicMock()
            mockResp.json.return_value = 'testAPIResponse'

            mockRepeatClient.get.return_value = mockResp
            testInstance.client = mockRepeatClient

        mockClientCreate = mocker.patch.object(NyplApiManager, 'createClient')
        mockClientCreate.side_effect = resetClient

        mockErrorClient = mocker.MagicMock()
        mockErrorClient.get.side_effect = TokenExpiredError
        testInstance.client = mockErrorClient

        mockTokenGenerate = mocker.patch.object(NyplApiManager, 'generateAccessToken')

        testResponse = testInstance.queryApi('test/path/request')

        assert testResponse == 'testAPIResponse'
        mockErrorClient.get.assert_called_once_with(
            'https://platform.nypl.org/api/v0.1/test/path/request', timeout=15
        )
        mockRepeatClient.get.assert_called_once_with(
            'https://platform.nypl.org/api/v0.1/test/path/request', timeout=15
        )
        mockTokenGenerate.assert_called_once
        mockClientCreate.assert_called_once

    def test_queyApi_timeout(self, testInstance, mocker):
        testInstance.client = mocker.MagicMock()
        testInstance.client.get.side_effect = TimeoutError
        
        assert testInstance.queryApi('test/path/request') == {}
        