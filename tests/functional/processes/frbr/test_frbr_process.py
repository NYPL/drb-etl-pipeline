from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess
from model import Record
from sqlalchemy import func

def test_frbr_process(db_manager, unfrbrized_record_uuid):
    classify_process = ClassifyProcess(
        'custom',
        None,
        datetime.now(timezone.utc) - timedelta(minutes=5),
        None
    )

    classify_process.runProcess()

    frbrized_record = db_manager.session.query(Record).filter(Record.uuid == unfrbrized_record_uuid).first()
    
    assert frbrized_record.frbr_status == 'complete'

    db_manager.session.commit()
    db_manager.session.expire_all()

    # Debug: Show all oclcClassify records
    test_records = db_manager.session.query(Record).filter(
        Record.source == 'oclcClassify'
    ).all()
    print(f"\nFound {len(test_records)} oclcClassify records:")
    for r in test_records:
        print(f" - ID: {r.id}, Source: {r.source}, Modified: {r.date_modified}")

    # Check timestamps
    current_time = datetime.utcnow()
    time_window = current_time - timedelta(minutes=2)
    print(f"\nCurrent UTC time: {current_time}")
    print(f"Time window threshold: {time_window}")

    classify_count = db_manager.session.query(Record).filter(
        Record.source == 'oclcClassify',
        Record.date_modified >= time_window
    ).count()
    
    assert classify_count >= 1, f"Expected oclcClassify records. Found: {classify_count}"
