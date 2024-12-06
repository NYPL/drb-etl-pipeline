from datetime import datetime, timezone, timedelta

from managers import DBManager
from model import Record
from processes.core import CoreProcess

def assert_ingested_records(source_name: str):
    db_manager = DBManager()
    db_manager.generateEngine()
    db_manager.createSession()

    doab_records = (
        db_manager.session.query(Record)
            .filter(Record.source == source_name)
            .filter(Record.date_modified > datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=5))
            .all()
    )

    assert len(doab_records) > 1
