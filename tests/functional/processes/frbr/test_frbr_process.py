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

    oclc_identifiers = [
        identifier 
        for identifier in new_record.identifiers 
        if identifier.endswith('|oclc')
    ]
    assert len(oclc_identifiers) > 0, \
        f"Missing OCLC identifiers in classified record: {new_record.identifiers}"

    catalog_process = CatalogProcess(
        None,
        None,
        None,
        None
    )
    catalog_process.runProcess(max_attempts=1)

    catalog_records = (
        db_manager.session.query(Record)
        .filter(
            Record.source == 'oclcCatalog',
            Record.source_id.in_(oclc_identifiers)
        )
        .all()
    )
    assert len(catalog_records) == len(oclc_identifiers), (
        f"Catalog record count mismatch. Expected {len(oclc_identifiers)}, "
        f"found {len(catalog_records)}. Missing: "
        f"{set(oclc_identifiers) - {r.source_id for r in catalog_records}}"
    )

    db_manager.session.close()
