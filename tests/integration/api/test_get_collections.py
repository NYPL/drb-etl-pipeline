import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/collections/3650664c-c8be-4d07-8d64-2d7003b02048", 200),
    ("/collections/00000000-0000-0000-0000-000000000000", 404),
    ("/collections/invalid_id_format", 400),
    ("/collections/", 404),
    ("/collections/%$@!*", 400)
])
def test_get_collections(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
