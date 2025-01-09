import pytest
import requests
from urllib.parse import quote
from .constants import API_URL

@pytest.mark.parametrize("endpoint", [
    ("/search?query=keyword:NASA&filter=format:readable")
])
def test_readable_format_flags(endpoint):
    url = API_URL + quote(endpoint)
    response = requests.get(url)
    
    response_json = response.json()
    assert response_json is not None, "Response JSON is empty"
    
    works = response_json.get('data', {}).get('works', [])
     
    for work in works:
        for edition in work.get('editions', []):
            for item in edition.get('items', []):
                if any(link.get('mediaType') == "text/html" for link in item.get('links', [])):
                    flags = item.get('links', [])[0].get('flags', {})
                    assert flags.get('reader', False) or flags.get('embed', False), \
                        f"Flags validation failed: {flags}"
