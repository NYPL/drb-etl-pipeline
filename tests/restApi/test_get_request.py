import requests
import pytest


BASE_URL = "https://drb-api-qa.nypl.org"
url = BASE_URL + "/collection/3650664c-c8be-4d07-8d64-2d7003b02048"

def test_get_request():
    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"

def test_collection_name():

    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"

    # Parse the JSON response
    data = response.json()

    # Validate the title in the metadata
    expected_title = "Works by Ayan"
    actual_title = data.get("metadata", {}).get("title", "")
    
    # Assert that the title is "Works by Ayan"
    assert actual_title == expected_title, f"Expected title '{expected_title}', but got '{actual_title}'"


def test_validate_json_fields():
   
    response = requests.get(url)
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}"

    # Parse the JSON response
    data = response.json()

    # Validate "numberOfItems" is 2
    assert data.get('metadata', {}).get('numberOfItems') == 2, f"Expected 'numberOfItems' to be 2, but got {data.get('metadata', {}).get('numberOfItems')}"

    # Validate the first title is "New Mexico magazine "
    first_publication_title = data.get('publications', [])[0].get('metadata', {}).get('title')
    assert first_publication_title == "New Mexico magazine ", f"Expected first title 'New Mexico magazine ', but got {first_publication_title}"

    # Validate the second title is "New Mexico magazine index. "
    second_publication_title = data.get('publications', [])[1].get('metadata', {}).get('title')
    assert second_publication_title == "New Mexico magazine index. ", f"Expected second title 'New Mexico magazine index. ', but got {second_publication_title}"
