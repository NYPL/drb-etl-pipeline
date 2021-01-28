from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
import os
from  time import time
from requests_oauthlib import OAuth2Session


class NyplApiManager:
    def __init__(self, clientID=None, clientSecret=None):
        super(NyplApiManager, self).__init__()
        self.client = None
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

    def createClient(self):
        self.client = OAuth2Session(self.clientID, token=self.token)

    def queryApi(self, requestPath):
        if not self.client: self.createClient()

        try:
            return self.client.get('{}/{}'.format(self.apiRoot, requestPath), timeout=15).json()
        except TokenExpiredError:
            self.generateAccessToken()
            self.client = None
            return self.queryApi(requestPath)
        except TimeoutError:
            return {}
