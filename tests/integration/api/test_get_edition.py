import pytest
import os
import requests
import json
from .utils import assert_response_status

API_URL = os.getenv("DRB_API_URL")

@pytest.mark.integration
@pytest.mark.parametrize("endpoint, expected_status", [
    ("/editions/{seeded_edition_id}", 200),
    ("/editions/00000000-0000-0000-0000-000000000000", 400),
    ("/editions/invalid_id_format", 400),
    ("/editions/", 404),
    ("/editions/%$@!*", 400)
])
def test_get_edition(endpoint, expected_status, seeded_edition_id): 
    url = API_URL + endpoint.format(seeded_edition_id=seeded_edition_id)
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, expected_status)

    if expected_status == 200:
        response_json = response.json()
        assert response_json is not None
