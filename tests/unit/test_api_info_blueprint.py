from flask import Flask
import pytest

from api.blueprints.drbInfo import apiInfo


class TestInfoBlueprint:
    def test_apiInfo(self, mocker):
        mocker.patch.dict('os.environ', {'ENVIRONMENT': 'test'})

        flaskApp = Flask('test')

        with flaskApp.test_request_context('/?testing=true'):
            apiResp, _ = apiInfo()
            assert apiResp.status_code == 200
            assert apiResp.get_json() == {'environment': 'test', 'status': 'RUNNING'}
