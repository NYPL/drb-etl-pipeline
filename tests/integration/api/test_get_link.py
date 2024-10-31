from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_collection():
    url = API_URL + '/link/1982731'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

