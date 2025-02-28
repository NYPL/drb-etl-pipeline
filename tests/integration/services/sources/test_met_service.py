
from services import METService


def test_get_records():
    gutenberg_service = METService()

    records = gutenberg_service.get_records(limit=100)

    for record in records:
        assert record is not None
