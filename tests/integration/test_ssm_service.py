import os
from load_env import load_env_file

from services.ssm_service import get_parameter

TEST_PARAM = 'arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/nypl-api/public-key'

def test_get_parameter():
    value = get_parameter(TEST_PARAM)

    assert value != None
