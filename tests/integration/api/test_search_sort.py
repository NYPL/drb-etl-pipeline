import pytest
import requests
from urllib.parse import quote
from .constants import API_URL

@pytest.mark.parametrize("endpoint, expected_language", [
    ("/search?query=keyword:NASA&sort=date:desc&filter=language:Serbian", "Serbian"),
])
def test_search_language_and_date_sorting(endpoint, expected_language):

    url = API_URL + quote(endpoint)
    response = requests.get(url)

    response_json = response.json()
    assert response_json is not None

        # Validate all results are in Serbian
    for item in response_json.get('results', []):
        assert item.get('language') == expected_language, f"Unexpected language: {item.get('language')}"
        
    publication_dates = [item.get('publication_date') for item in response_json.get('results', [])]
    assert all(date is not None for date in publication_dates), \
            f"Some publication dates are missing: {publication_dates}"
    assert publication_dates == sorted(publication_dates, reverse=True), \
            f"Publication dates are not sorted in descending order: {publication_dates}"
