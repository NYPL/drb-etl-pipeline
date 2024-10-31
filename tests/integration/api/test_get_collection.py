from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_collection():
    url = API_URL + '/collection/3650664c-c8be-4d07-8d64-2d7003b02048'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None
