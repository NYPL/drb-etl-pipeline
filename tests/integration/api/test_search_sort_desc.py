import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/search?query=keyword%3ANASA&sort=date%3Adesc&filter=language%3ASerbian", 200),
])
def test_search_language_and_date_sorting(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None

        for item in response_json.get('results', []):
            assert item.get('language') == 'Serbian', f"Unexpected language: {item.get('language')}"

        previous_date = None
        for item in response_json.get('results', []):
            current_date = item.get('publication_date')
            assert current_date is not None, "Publication date is missing"
            
            if previous_date:
                assert current_date >= previous_date, f"Publication dates are not sorted in descending order: {previous_date} > {current_date}"
            
            previous_date = current_date
