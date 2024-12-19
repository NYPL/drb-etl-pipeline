import pytest
import requests
from .constants import API_URL
from .utils import assert_response_status

@pytest.mark.parametrize("endpoint, expected_status", [
    ("/editions/1982731", 200),
    ("/editions/00000000-0000-0000-0000-000000000000", 400),
    ("/editions/invalid_id_format", 400),
    ("/editions/", 404),
    ("/editions/%$@!*", 400)
])
def test_get_editions(endpoint, expected_status):
    url = API_URL + endpoint
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
