from services import LOCService


def test_get_records():
    loc_service = LOCService()

    records = loc_service.get_records(limit=1)

    for record in records:
        assert record is not None
