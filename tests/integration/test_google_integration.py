import os
import pytest
from load_env import load_env_file
from services import GoogleDriveService

load_env_file('local-compose', file_string='config/local-compose.yaml')

class TestGoogleDriveService:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return GoogleDriveService()

    def test_get_drive_file(self, test_instance: GoogleDriveService):
        TEST_FILE_ID = '1GBskazIv6j2BjOolNYqJKKIJC8iYhTcs'
        file = test_instance.get_drive_file(TEST_FILE_ID)

        assert file != None
        assert file.seek(0, 2) > 1
