from datetime import datetime, timezone, timedelta
import pytest

from load_env import load_env_file
from services import NYPLBibService

class TestNYPLBibService:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return NYPLBibService()

    def test_get_records(self, test_instance: NYPLBibService):
        records = test_instance.get_records(
            start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24), 
            limit=100
        )

        assert records is not None
