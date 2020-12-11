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

    def test_tokenSaver(self, testInstance):
        testInstance.tokenSaver({})

        assert testInstance.token == {'expires_in': 900}

    def test_queryApi(self, testInstance, mocker):
        mockOauthSession = mocker.patch('managers.nyplApi.OAuth2Session')
        mockClient = mocker.MagicMock()
        mockResp = mocker.MagicMock()
        mockResp.json.return_value = 'testAPIResponse'
        mockClient.get.return_value = mockResp
        mockOauthSession.return_value = mockClient

        testResponse = testInstance.queryApi('test/path/request')

        assert testResponse == 'testAPIResponse'
        mockOauthSession.assert_called_once_with('test_api_client',
            token=None, auto_refresh_url='test_api_token_url',
            auto_refresh_kwargs={'client_id': 'test_api_client', 'client_secret': 'test_api_secret'},
            token_updater=testInstance.tokenSaver
        )
        mockClient.get.assert_called_once_with('https://platform.nypl.org/api/v0.1/test/path/request')
        