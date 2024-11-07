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

def test_get_collection_non_existent_id():
    url = API_URL + '/collection/00000000-0000-0000-0000-000000000000'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_collection_malformed_id():
    url = API_URL + '/collection/invalid_id_format'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_collection_empty_id():
    url = API_URL + '/collection/'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_collection_special_characters():
    url = API_URL + '/collection/%$@!*'
    response = requests.get(url)
    assert_response_status(url, response, 400)