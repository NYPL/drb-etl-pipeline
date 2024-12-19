import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/works/701c5f00-cd7a-4a7d-9ed1-ce41c574ad1d", 200),
    ("/works/00000000-0000-0000-0000-000000000000", 404),
    ("/works/invalid_id_format", 400),
    ("/works/", 404),
    ("/works/%$@!*", 400)
])
def test_get_works(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
