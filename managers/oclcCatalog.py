import os
import requests
from requests.exceptions import Timeout, ConnectionError

class OCLCCatalogManager:
    CATALOG_URL = 'http://www.worldcat.org/webservices/catalog/content/{}?wskey={}'
    OCLC_AUTH_URL = 'https://oauth.oclc.org/token?scope=wcapi&grant_type=client_credentials'
    OCLC_SEARCH_URL = 'https://americas.discovery.api.oclc.org/worldcat/search/v2/'
    # TODO: don't have init param oclcNo
    def __init__(self, oclcNo):
        self.oclcNo = oclcNo
        self.oclcKey = os.environ['OCLC_API_KEY']
        self.oclcClientID = os.environ['OCLC_CLIENT_ID']
        self.oclcClientSecret = os.environ['OCLC_CLIENT_SECRET']
        self.attempts = 0
        self.token = None
        self.tokenExpiresAt = None

    # TODO: pass in oclcNo
    def queryCatalog(self):
        classifyResp = None
        self.attempts += 1
        catalogQuery = self.CATALOG_URL.format(self.oclcNo, self.oclcKey)
        if self.attempts > 3:
            return classifyResp

        try:
            classifyResp = requests.get(catalogQuery, timeout=3)
        except (Timeout, ConnectionError):
            print('Failed to query URL {}'.format(catalogQuery))
            return self.queryCatalog()

        if classifyResp.status_code != 200:
            print('OCLC Catalog Request failed with status {}'.format(
                classifyResp.status_code
            ))
            return None

        return classifyResp.text

    def getToken(self):
        try:
            authResp = requests.post(
                self.OCLC_AUTH_URL,
                headers={ 'Content-Type': 'application/x-www-form-urlencoded'},
                auth=(self.oclcClientID, self.oclcClientSecret),
            )
        except (Timeout, ConnectionError):
            print(f'Failed to retrieve token from {self.OCLC_AUTH_URL}')
            return None

        if authResp.status_code != 200:
            print('OCLC token retrieval failed with status {}'.format(
                authResp.status_code
            ))
            return None

        self.token = authResp.json()['access_token']
        self.tokenExpiresAt = authResp.json()['expires_at']

    def queryBriefBibs(self, query):
        """Accepts a query in the form of an OCLC keyword search or fielded search"""
        self.getToken()
        bibsEndpoint = self.OCLC_SEARCH_URL + 'brief-bibs'

        headers = {"Authorization": f"Bearer {self.token}"}
        try:
            bibsResp = requests.get(
                bibsEndpoint,
                headers=headers,
                params={'q': query}
            )
        except (Timeout, ConnectionError):
            print(f'Failed to query {bibsEndpoint} with query {query}')
            return self.queryCatalog()

        if bibsResp.status_code != 200:
            print(f'OCLC Catalog Request failed with status {bibsResp.status_code}')
            return None

        return bibsResp.json()