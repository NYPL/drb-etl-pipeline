import os
from load_env import load_env_file

load_env_file('local-compose', file_string='config/local-compose.yaml')

from services.google_drive_service import get_drive_file

TEST_FILE_ID = '1GBskazIv6j2BjOolNYqJKKIJC8iYhTcs'

def test_get_drive_file():
    file = get_drive_file(TEST_FILE_ID)

    assert file != None
    assert file.seek(0, 2) > 1
