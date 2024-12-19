import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/link/1982731", 200),
    ("/link/00000000-0000-0000-0000-000000000000", 400),
    ("/link/invalid_id_format", 400),
    ("/link/", 404),
    ("/link/%$@!*", 400)
])
def test_get_link(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
