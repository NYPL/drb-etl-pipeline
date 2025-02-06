import pytest
from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess
from model import Record


def test_frbr_process(db_manager, seed_unfrbrized_record):
    classify_process = ClassifyProcess(
        'custom',
        None,
        None,
        seed_unfrbrized_record,
        int((datetime.now(timezone.utc) - timedelta(minutes=5)).timestamp())
    )
    classify_process.runProcess()

    original_record = db_manager.session.query(Record).filter(
        Record.uuid == seed_unfrbrized_record
    ).first()
    assert original_record.frbr_status == 'complete', "FRBRization failed"
