import pytest
import requests
from urllib.parse import quote
from .constants import API_URL

@pytest.mark.parametrize("endpoint", [
    ("/search?query=keyword:NASA&filter=format:readable"),
    ("/search?query=keyword:NASA&filter=format:downloadable")
])
def test_readable_format_flags(endpoint):
    url = API_URL + quote(endpoint)
    response = requests.get(url)
    
    response_json = response.json()
    assert response_json is not None, "Response JSON is empty"
    
    works = response_json.get('data', {}).get('works', [])

    is_downloadable = "format=downloadable" in endpoint
     
    for work in works:
        for edition in work.get('editions', []):
            for item in edition.get('items', []):
                html_links = [link for link in item.get('links', []) if link.get('mediaType') == "text/html"]
            for link in html_links:
                flags = link.get('flags', {})
                assert flags.get('reader', False) or flags.get('embed', False), \
                    f"HTML link validation failed for flags: {flags}"
        
            other_links = [link for link in item.get('links', []) if link.get('mediaType') != "text/html"]
            for link in other_links:
                flags = link.get('flags', {})
                assert flags.get('reader', True), \
                    f"Non-HTML link validation failed for flags: {flags}"
                
        if is_downloadable:
            downloadable_links = [link for link in item.get('links', [])]
            for link in downloadable_links:
                flags = link.get('flags', {})
                assert flags.get('downloadable', False), \
                            f"Downloadable flag validation failed for flags: {flags}"
