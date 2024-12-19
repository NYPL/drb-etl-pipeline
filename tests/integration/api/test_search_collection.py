from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_search():
    url = API_URL + '/search?query=keyword%3Abaseball&page=1&size=5&readerVersion=v1'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

def test_get_search_non_existent_id():
    url = API_URL + '/search/00000000-0000-0000-0000-000000000000'
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