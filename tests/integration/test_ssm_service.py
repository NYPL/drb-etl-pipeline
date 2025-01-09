import os
import pytest
from load_env import load_env_file

from services import SSMService

class TestSSMService:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return SSMService()

    def test_get_parameter(self, test_instance):
        TEST_PARAM = 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/nypl-api/public-key'
        value = test_instance.get_parameter(TEST_PARAM)

        assert value != None
