from oauthlib.oauth2 import BackendApplicationClient
import os
import requests
from requests_oauthlib import OAuth2Session


class NyplApiManager:
    def __init__(self, clientID=None, clientSecret=None):
        super(NyplApiManager, self).__init__()
        self.clientID = clientID or os.environ['API_CLIENT_ID']
        self.clientSecret = clientSecret or os.environ['API_CLIENT_SECRET']
        self.tokenURL = os.environ['API_CLIENT_TOKEN_URL']
        self.apiRoot = 'https://platform.nypl.org/api/v0.1'
        self.token = None

    def generateAccessToken(self):
        client = BackendApplicationClient(self.clientID)
        oauth = OAuth2Session(client=client)
        self.token = oauth.fetch_token(
            token_url=self.tokenURL,
            client_id=self.clientID,
            client_secret=self.clientSecret
        )

    def tokenSaver(self, token):
        self.token = token
        self.token['expires_in'] = 900

    def queryApi(self, requestPath):
        client = OAuth2Session(self.clientID,
            token=self.token,
            auto_refresh_url=self.tokenURL,
            auto_refresh_kwargs={'client_id': self.clientID, 'client_secret': self.clientSecret},
            token_updater=self.tokenSaver
        )

        return client.get('{}/{}'.format(self.apiRoot, requestPath)).json()
