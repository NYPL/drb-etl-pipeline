import requests
import pytest

BASE_URL = "https://drb-api-qa.nypl.org"

def test_get_collection():
    url = BASE_URL + "/collection/3650664c-c8be-4d07-8d64-2d7003b02048"
    expected_status_code = 200
    response = requests.get(url)
    assert expected_status_code is not None
    assert response.status_code == expected_status_code, (
        f"API call failed.\n"
        f"Expected status code: {expected_status_code}\n"
        f"Actual status code: {response.status_code}\n"
        f"URL: {url}\n"
        f"Response text: {response.text[:100]}..."
    )
    
    response_json = response.json()
    assert response_json is not None
