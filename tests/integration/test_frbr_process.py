import pytest
from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess
from model import Record


def test_frbr_process(db_manager, seed_unclassified_record):
    record_uuid = seed_unclassified_record
    
    classify_process = ClassifyProcess(
        'custom',
        None,
        None,
        record_uuid,
        int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp())
    )
    classify_process.runProcess()

    original_record = db_manager.session.query(Record).filter(
        Record.uuid == record_uuid
    ).first()
    assert original_record.frbr_status == 'complete', "FRBRization failed"
