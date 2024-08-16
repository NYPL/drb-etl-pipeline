import os
import requests
from requests.exceptions import Timeout, ConnectionError
from typing import Optional

from logger import createLog
from managers.oclc_auth import OCLCAuthManager


logger = createLog(__name__)


class OCLCCatalogManager:
    """Manages creation and execution of queries to the OCLC Catalog
        Search and Metadata APIs.
    Raises:
        DataError: Raised when an invalid title/author query is attempted
        OCLCError: Raised when the query to the API fails
    """
    CATALOG_URL = 'http://www.worldcat.org/webservices/catalog/content/{}?wskey={}'
    OCLC_SEARCH_URL = 'https://americas.discovery.api.oclc.org/worldcat/search/v2/'

    def __init__(self):
        self.oclcKey = os.environ['OCLC_API_KEY']
        self.attempts = 0

    def query_catalog(self, oclcNo):
        catalog_response = None
        self.attempts += 1
        catalog_query = self.CATALOG_URL.format(oclcNo, self.oclcKey)

        if self.attempts > 3:
            return catalog_response

        try:
            catalog_response = requests.get(catalog_query, timeout=3)
        except (Timeout, ConnectionError):
            logger.warn(f'Failed to query URL {catalog_query}')
            return self.query_catalog(oclcNo)

        if catalog_response.status_code != 200:
            logger.warn(f'OCLC Catalog Request failed with status {catalog_response.status_code}')
            return None

        return catalog_response.text

    def get_related_oclc_numbers(self, oclc_number: int) -> Optional[list[int]]:
        other_editions_url = f'https://americas.discovery.api.oclc.org/worldcat/search/v2/brief-bibs/{oclc_number}/other-editions'

        try:
            token = OCLCAuthManager.get_token()
            headers = { 'Authorization': f'Bearer {token}' }

            # TODO: SFR-2090, SFR-2091 Determine how many records to get and how to order
            other_editions_response = requests.get(
                other_editions_url,
                headers=headers,
                params={
                    'limit': 10,
                    'orderBy': 'bestMatch'
                }
            )
        except Exception as e:
            logger.error(f'Failed to query URL {other_editions_url} due to {e}')
            return None

        if other_editions_response.status_code != 200:
            logger.warn(f'OCLC other editions request failed with status {other_editions_response.status_code}')
            return None

        brief_records = other_editions_response.json().get('briefRecords', None)

        if not brief_records:
            return None

        return [int(brief_record['oclcNumber']) for brief_record in brief_records if int(brief_record['oclcNumber']) != oclc_number]


    def query_brief_bibs(self, query: str):
        """Accepts a query in the form of an OCLC keyword search or fielded search"""
        token = OCLCAuthManager.get_token()
        bibs_endpoint = self.OCLC_SEARCH_URL + 'brief-bibs'
        # Limit 10 results, ordered by bestMatch, by default
        headers = { "Authorization": f"Bearer {token}" }
        try:
            bibs_response = requests.get(
                bibs_endpoint,
                headers=headers,
                params={'q': query}
            )
        except (Timeout, ConnectionError):
            logger.warn(f'Failed to query {bibs_endpoint} with query {query}')
            raise OCLCError(f'Failed to query {bibs_endpoint} with query {query}')

        if bibs_response.status_code != 200:
            logger.warn(f'OCLC Catalog Request failed with status {bibs_response.status_code}')
            raise OCLCError(f'OCLC Catalog Request failed with status {bibs_response.status_code}')

        return bibs_response.json()

class OCLCError(Exception):
    def __init__(self, message=None):
        self.message = message