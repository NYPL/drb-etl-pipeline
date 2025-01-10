from datetime import datetime, timezone, timedelta
import pytest

from services import PublisherBacklistService

class TestPublisherBacklistService:
    @pytest.fixture
    def test_instance(self):
        return PublisherBacklistService()

    def test_get_records(self, test_instance: PublisherBacklistService):
        records = test_instance.get_records(
            start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7), 
            limit=100
        )

        assert records is not None
