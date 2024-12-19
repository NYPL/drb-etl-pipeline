import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/collection/3650664c-c8be-4d07-8d64-2d7003b02048", 200),
    ("/collection/00000000-0000-0000-0000-000000000000", 404),
    ("/collection/invalid_id_format", 400),
    ("/collection/", 404),
    ("/collection/%$@!*", 400)
])
def test_get_collection(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
