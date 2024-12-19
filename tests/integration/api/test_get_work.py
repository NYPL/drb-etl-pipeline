from .constants import API_URL
from .utils import assert_response_status
import requests


def test_get_work():
    url = API_URL + '/work/701c5f00-cd7a-4a7d-9ed1-ce41c574ad1d'
    response = requests.get(url)

    assert response.status_code is not None
    assert_response_status(url, response, 200)

    response_json = response.json()
    
    assert response_json is not None

def test_get_work_non_existent_id():
    url = API_URL + '/work/00000000-0000-0000-0000-000000000000'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_work_malformed_id():
    url = API_URL + '/work/invalid_id_format'
    response = requests.get(url)
    assert_response_status(url, response, 400)

def test_get_work_empty_id():
    url = API_URL + '/work/'
    response = requests.get(url)
    assert_response_status(url, response, 404)

def test_get_work_special_characters():
    url = API_URL + '/work/%$@!*'
    response = requests.get(url)
    assert_response_status(url, response, 400)
