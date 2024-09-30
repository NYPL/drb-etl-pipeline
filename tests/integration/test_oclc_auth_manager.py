from managers.oclc_auth import OCLCAuthManager
from load_env import load_env_file

load_env_file('local-compose', file_string='config/local-compose.yaml')


def test_get_search_token():
    token = OCLCAuthManager.get_search_token()

    assert token != None


def test_reuse_valid_search_token():
    token = OCLCAuthManager.get_search_token()
    new_token = OCLCAuthManager.get_search_token()

    assert new_token == token

def test_get_metadata_token():
    token = OCLCAuthManager.get_metadata_token()

    assert token != None

def test_reuse_valid_metadata_token():
    token = OCLCAuthManager.get_metadata_token()
    new_token = OCLCAuthManager.get_metadata_token()

    assert new_token == token
