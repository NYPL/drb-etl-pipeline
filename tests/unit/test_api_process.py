import pytest

from tests.helper import TestHelpers
from processes import APIProcess


class TestAPIProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def apiInstance(self, mocker):
        mocker.patch.object(APIProcess, 'createElasticConnection')
        mocker.patch.object(APIProcess, 'generateEngine')
        mockAPI = mocker.MagicMock()
        mockFlask = mocker.patch('processes.api.FlaskAPI')
        mockFlask.return_value = mockAPI

        return APIProcess('TestProcess', 'testFile', 'testDate', 'testRecord')
    
    def test_api_runProcess(self, apiInstance, mocker):
        apiInstance.runProcess()
        apiInstance.api.run.assert_called_once
