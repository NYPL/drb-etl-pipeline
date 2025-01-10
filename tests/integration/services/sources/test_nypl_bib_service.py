from datetime import datetime, timezone, timedelta
import pytest

from services import NYPLBibService

class TestNYPLBibService:
    @pytest.fixture
    def test_instance(self):
        return NYPLBibService()

    def test_get_records(self, test_instance: NYPLBibService):
        records = test_instance.get_records(
            start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24), 
            limit=100
        )

        assert records is not None
