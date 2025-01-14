import pytest
import requests
from .constants import API_URL

@pytest.mark.parametrize('endpoint', [
    ('/search?query=keyword:NASA&filter=format:readable'),
    ('/search?query=keyword:NASA&filter=format:downloadable')
])
def test_readable_format_flags(endpoint):
    url = API_URL + endpoint
    response = requests.get(url)
    
    response_json = response.json()
    assert response_json is not None, 'Response JSON is empty'
    assert response.status_code == 200
    
    works = response_json.get('data', {}).get('works', [])

    is_downloadable = 'format=downloadable' in endpoint
    is_readable = 'format=readable' in endpoint

    links = [
        link for work in works for edition in work.get('editions', []) 
        for item in edition.get('items', []) 
        for link in item.get('links', [])
    ]

    for link in links:
        flags = link.get('flags', {})

        if is_readable:
            assert flags.get('reader', False) or flags.get('embed', False)

        if is_downloadable:
            assert flags.get('downloadable', False)
