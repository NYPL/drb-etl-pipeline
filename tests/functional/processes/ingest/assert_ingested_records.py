from datetime import datetime, timezone, timedelta
from typing import Optional

from managers import DBManager
from model import Record


def assert_ingested_records(source_name: str, expected_number_of_records: Optional[int]=None) -> list[Record]:
    db_manager = DBManager()
    db_manager.generateEngine()
    db_manager.createSession()

    records = (
        db_manager.session.query(Record)
            .filter(Record.source == source_name)
            .filter(Record.date_modified > datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5))
            .all()
    )

    if expected_number_of_records is not None:
        assert len(records) == expected_number_of_records
    else:
        assert len(records) >= 1

    return records
