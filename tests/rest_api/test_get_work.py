import requests
import pytest

BASE_URL = "https://drb-api-qa.nypl.org"

def test_get_collection():

    url = BASE_URL + "/work/701c5f00-cd7a-4a7d-9ed1-ce41c574ad1d"
    response = requests.get(url)

    assert response.status_code is not None
    assert response.status_code == 200, (
        f"API call failed.\n"
        f"Expected status code: {200}\n"
        f"Actual status code: {response.status_code}\n"
        f"URL: {url}\n"
        f"Response text: {response.text[:100]}..."
    )

    response_json = response.json()
    
    assert response_json is not None

