from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_edition():
    url =  API_URL + '/edition/1982731'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

def test_get_edition_non_existent_id():
    url = API_URL + '/edition/00000000-0000-0000-0000-000000000000'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_edition_malformed_id():
    url = API_URL + '/edition/invalid_id_format'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_edition_empty_id():
    url = API_URL + '/edition/'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_edition_special_characters():
    url = API_URL + '/edition/%$@!*'
    response = requests.get(url)
    assert_response_status(url, response, 400)
    