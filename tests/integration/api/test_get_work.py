from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_collection():
    url = API_URL + '/work/701c5f00-cd7a-4a7d-9ed1-ce41c574ad1d'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

