from datetime import datetime, timezone, timedelta
import pytest

from load_env import load_env_file
from services import PublisherBacklistService

class TestPublisherBacklistService:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local', file_string='config/local.yaml')
        return PublisherBacklistService()

    def test_get_records(self, test_instance: PublisherBacklistService):
        records = test_instance.get_records(
            start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7), 
            limit=100
        )

        assert records is not None
