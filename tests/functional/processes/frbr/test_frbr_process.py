from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess
from model import Record

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
    db_manager.session.refresh(frbrized_record)

    assert any(id.endswith('|owi') for id in frbrized_record.identifiers), \
        f"Missing OWI identifier after classification. Current IDs: {frbrized_record.identifiers}" #test is failing because indentifier field is not getting updated after classifying

    current_time = datetime.utcnow()
    time_window = current_time - timedelta(minutes=2)

    classify_count = db_manager.session.query(Record).filter(Record.source == 'oclcClassify', Record.date_modified >= time_window).count()

    assert classify_count >= 1, f"Expected oclcClassify records. Found: {classify_count}"
