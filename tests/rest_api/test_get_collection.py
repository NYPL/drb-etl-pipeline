import requests
import pytest


BASE_URL = "https://drb-api-qa.nypl.org"

def test_get_collection():

    url = BASE_URL + "/collection/3650664c-c8be-4d07-8d64-2d7003b02048"
    expected_status_code = 200
    response = requests.get(url)
    assert response.status_code == expected_status_code, (
        f"API call failed.\n"
        f"Expected status code: {expected_status_code}\n"
        f"Actual status code: {response.status_code}\n"
        f"URL: {url}\n"
        f"Response text: {response.text[:100]}..."
    )

    data = response.json()

    expected_title = "Works by Ayan"
    actual_title = data.get("metadata", {}).get("title", "")
   
    assert actual_title == expected_title, f"Expected title '{expected_title}', but got '{actual_title}'"

    first_publication_title = data.get('publications', [])[0].get('metadata', {}).get('title')
    assert first_publication_title == "New Mexico magazine ", f"Expected first title 'New Mexico magazine ', but got {first_publication_title}"

    second_publication_title = data.get('publications', [])[1].get('metadata', {}).get('title')
    assert second_publication_title == "New Mexico magazine index. ", f"Expected second title 'New Mexico magazine index. ', but got {second_publication_title}"
