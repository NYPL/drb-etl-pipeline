from oauthlib.oauth2 import BackendApplicationClient, TokenExpiredError
import os
from requests_oauthlib import OAuth2Session
from services.ssm_service import SSMService


class NyplApiManager:
    def __init__(self, clientID=None, clientSecret=None):
        super(NyplApiManager, self).__init__()

        self.ssm_service = SSMService()
        self.client = None
        self.clientID = clientID or self.ssm_service.get_parameter('nypl-api/client-id')
        self.clientSecret = clientSecret or self.ssm_service.get_parameter('nypl-api/client-secret')
        self.tokenURL = 'https://isso.nypl.org/oauth/token'
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
        if not self.client:
            self.createClient()

        try:
            return self.client.get(
                '{}/{}'.format(self.apiRoot, requestPath),
                timeout=15
            ).json()
        except TokenExpiredError:
            self.generateAccessToken()
            self.client = None

            return self.queryApi(requestPath)
        except TimeoutError:
            return {}
