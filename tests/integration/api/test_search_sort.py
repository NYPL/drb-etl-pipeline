import pytest
import requests
from urllib.parse import quote
from .constants import API_URL

@pytest.mark.parametrize("endpoint, expected_language, sort_field, sort_order", [
    ("/search?query=keyword:NASA&sort=date:desc&filter=language:Serbian", "Serbian", "publication_date", "desc"),
    ("/search?query=keyword:NASA&sort=date:asc&filter=language:Serbian", "Serbian", "publication_date", "asc"),
    ("/search?query=keyword:NASA&sort=author:desc&filter=language:Serbian", "Serbian", "author", "desc"),
    ("/search?query=keyword:NASA&sort=author:asc&filter=language:Serbian", "Serbian", "author", "asc")
])
def test_search_language_and_sorting(endpoint, expected_language, sort_field, sort_order):
    url = API_URL + quote(endpoint)
    response = requests.get(url)

    response_json = response.json()
    assert response_json is not None, "Response JSON is empty"

    for item in response_json.get('results', []):
        assert item.get('language') == expected_language, f"Unexpected language: {item.get('language')}"

    sort_values = [item.get(sort_field) for item in response_json.get('results', [])]
    assert all(value is not None for value in sort_values), \
        f"Some {sort_field} values are missing: {sort_values}"
    
    if sort_order == "desc":
        assert sort_values == sorted(sort_values, reverse=True), \
            f"{sort_field.capitalize()} values are not sorted in descending order: {sort_values}"
    elif sort_order == "asc":
        assert sort_values == sorted(sort_values), \
            f"{sort_field.capitalize()} values are not sorted in ascending order: {sort_values}"
