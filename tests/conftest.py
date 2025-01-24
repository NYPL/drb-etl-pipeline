import os
import pytest

from load_env import load_env_file


def pytest_addoption(parser):
    parser.addoption('--env', action='store', default='local', help='Environment to use for tests')


@pytest.fixture(scope='session', autouse=True)
def setup_env(pytestconfig):
    environment = os.environ.get('ENVIRONMENT') or pytestconfig.getoption('--env') or 'local'

    if environment in ['local', 'qa']:
        load_env_file(environment, file_string=f'config/{environment}.yaml')
