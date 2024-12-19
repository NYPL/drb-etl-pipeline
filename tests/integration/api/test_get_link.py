from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_link():
    url = API_URL + '/link/1982731'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

def test_get_link_non_existent_id():
    url = API_URL + '/link/00000000-0000-0000-0000-000000000000'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_link_malformed_id():
    url = API_URL + '/link/invalid_id_format'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_link_empty_id():
    url = API_URL + '/link/'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_link_special_characters():
    url = API_URL + '/link/%$@!*'
    response = requests.get(url)
    assert_response_status(url, response, 400)
