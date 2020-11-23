import os
import re
import requests
from requests.exceptions import Timeout, ConnectionError, ReadTimeout

class OCLCCatalogManager:
    CATALOG_URL = 'http://www.worldcat.org/webservices/catalog/content/{}?wskey={}'
    def __init__(self, oclcNo):
        self.oclcNo = oclcNo
        self.oclcKey = os.environ['OCLC_API_KEY']
        self.attempts = 0

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
            self.queryCatalog()

        if classifyResp is None:
            return None
        elif classifyResp.status_code != 200:
            print('OCLC Catalog Request failed with status {}'.format(
                classifyResp.status_code
            ))
            return None
    
        return classifyResp.text
        
   