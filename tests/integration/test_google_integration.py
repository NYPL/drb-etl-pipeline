import os
from load_env import load_env_file

load_env_file('local-compose', file_string='config/local-compose.yaml')

from processes.util.google_integration import get_drive_file

def test_get_drive_file():
    test_id = os.environ['EXAMPLE_FILE_ID']
    file = get_drive_file(test_id)

    assert file != None
    print(file.seek(0, 2))
    assert file.seek(0, 2) > 1

