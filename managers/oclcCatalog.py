import os
import requests
from requests.exceptions import Timeout, ConnectionError

class OCLCCatalogManager:
    CATALOG_URL = 'http://www.worldcat.org/webservices/catalog/content/{}?wskey={}'
    OCLC_AUTH_URL = 'https://oauth.oclc.org/token?scope=wcapi&grant_type=client_credentials'
    # TODO: don't have init param oclcNo
    def __init__(self, oclcNo):
        self.oclcNo = oclcNo
        self.oclcKey = os.environ['OCLC_API_KEY']
        self.oclcClientID = os.environ['OCLC_CLIENT_ID']
        self.oclcClientSecret = os.environ['OCLC_CLIENT_SECRET']
        self.attempts = 0

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

    def new_query(self):
        auth_response = requests.post(
            self.OCLC_AUTH_URL,
            headers={ 'Content-Type': 'application/x-www-form-urlencoded' },
            auth=(self.oclcClientID, self.oclcClientSecret),
        )

        print(auth_response)
        # TODO:
        # 1. auth
        # 2. bibs endpoint

