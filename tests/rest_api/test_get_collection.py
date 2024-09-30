import requests
import pytest

BASE_URL = "https://drb-api-qa.nypl.org"

def test_get_collection():

    url = BASE_URL + "/collection/3650664c-c8be-4d07-8d64-2d7003b02048"
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
