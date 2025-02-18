from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess, CatalogProcess
from model import Record


def test_frbr_process(db_manager, unfrbrized_record_uuid, unfrbrized_title):
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

    current_time = datetime.utcnow()
    time_window = current_time - timedelta(minutes=2)

    classify_count = db_manager.session.query(Record).filter(Record.source == 'oclcClassify', Record.date_modified >= time_window).count()

    assert classify_count >= 1, f"Expected oclcClassify records. Found: {classify_count}"

    new_record = (
        db_manager.session.query(Record)
        .filter(
            Record.source == 'oclcClassify',
            Record.title.ilike(f"%{unfrbrized_title}%"))
        .order_by(Record.date_created.desc())
        .first())
    
    assert new_record is not None, f"No record found containing title: '{unfrbrized_title}'"

    assert new_record.source_id.endswith('|owi'), \
        f"Expected OWI source ID, got: {new_record.source_id}"

    oclc_identifiers = [id.split('|')[0] for id in new_record.identifiers if id.endswith('|oclc')]
    assert len(oclc_identifiers) > 0, f"No OCLC numbers found in: {new_record.identifiers}"

    catalog_process = CatalogProcess(
        None,
        None,
        None,
        None
    )

    catalog_process.runProcess(max_attempts=1)

    new_catalog_records = db_manager.session.query(Record).filter(
        Record.source == 'oclcCatalog',
        Record.date_created >= datetime.now(timezone.utc) - timedelta(minutes=1)
    ).all()

    matching_records = [
        record for record in new_catalog_records
        if any(oclc_id in record.identifiers for oclc_id in oclc_identifiers)
    ]
    
    assert len(matching_records) > 0, (
        f"No catalog records matched expected OCLC identifiers. "
        f"No catalog records matched OCLC identifiers: {oclc_identifiers}"
        f"Found in catalog records: {[r.identifiers for r in new_catalog_records]}"
    )

    db_manager.session.close()
