import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/search?query=keyword%3Abaseball&page=1&size=5&readerVersion=v1", 200),
    ("/search/00000000-0000-0000-0000-000000000000", 404),
    ("/search/invalid_id_format", 404),
    ("/search/", 404),
    ("/search/%$@!*", 404)
])
def test_search(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
