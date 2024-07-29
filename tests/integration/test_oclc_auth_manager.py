from managers.oclcAuth import OCLCAuthManager
from loadEnv import loadEnvFile
import os

loadEnvFile('local-compose', fileString='config/local-compose.yaml')


def test_get_token():
    token = OCLCAuthManager.getToken()

    assert token != None


def test_reuse_valid_token():
    token = OCLCAuthManager.getToken()
    new_token = OCLCAuthManager.getToken()

    assert new_token == token
