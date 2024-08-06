import os
import requests
from requests.exceptions import Timeout, ConnectionError

from logger import createLog
from managers.oclcAuth import OCLCAuthManager


logger = createLog(__name__)


class OCLCCatalogManager:
    CATALOG_URL = 'http://www.worldcat.org/webservices/catalog/content/{}?wskey={}'
    OCLC_SEARCH_URL = 'https://americas.discovery.api.oclc.org/worldcat/search/v2/'
    def __init__(self):
        self.oclcKey = os.environ['OCLC_API_KEY']
        self.attempts = 0

    def queryCatalog(self, oclcNo):
        classifyResp = None
        self.attempts += 1
        catalogQuery = self.CATALOG_URL.format(oclcNo, self.oclcKey)
        if self.attempts > 3:
            return classifyResp

        try:
            classifyResp = requests.get(catalogQuery, timeout=3)
        except (Timeout, ConnectionError):
            logger.warn('Failed to query URL {}'.format(catalogQuery))
            return self.queryCatalog(oclcNo)

        if classifyResp.status_code != 200:
            logger.warn('OCLC Catalog Request failed with status {}'.format(
                classifyResp.status_code
            ))
            return None

        return classifyResp.text

    def queryBriefBibs(self, query):
        """Accepts a query in the form of an OCLC keyword search or fielded search"""
        token = OCLCAuthManager.getToken()
        bibsEndpoint = self.OCLC_SEARCH_URL + 'brief-bibs'

        headers = {"Authorization": f"Bearer {token}"}
        try:
            # Limit 10 results, ordered by bestMatch, by default
            bibsResp = requests.get(
                bibsEndpoint,
                headers=headers,
                params={'q': query}
            )
        except (Timeout, ConnectionError):
            logger.warn(f'Failed to query {bibsEndpoint} with query {query}')
            return self.queryCatalog()

        if bibsResp.status_code != 200:
            logger.warn(f'OCLC Catalog Request failed with status {bibsResp.status_code}')
            return None

        return bibsResp.json()
