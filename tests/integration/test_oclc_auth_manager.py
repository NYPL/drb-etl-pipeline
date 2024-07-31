from managers.oclc_auth import OCLCAuthManager
from load_env import load_env_file

load_env_file('local-compose', file_string='config/local-compose.yaml')


def test_get_token():
    token = OCLCAuthManager.get_token()

    assert token != None


def test_reuse_valid_token():
    token = OCLCAuthManager.get_token()
    new_token = OCLCAuthManager.get_token()

    assert new_token == token
