from datetime import datetime, timedelta, timezone
from processes import ClassifyProcess, CatalogProcess
from managers import OCLCCatalogManager, RabbitMQManager
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
        .filter(Record.title.ilike(f"%{unfrbrized_title}%"))
        .order_by(Record.date_created.desc())
        .first())
    
    if not new_record:
        pytest.fail(f"No record found containing title: '{unfrbrized_title}'")

    # Verify OWI in identifiers instead of source_id
    assert any(id.endswith('|owi') for id in new_record.identifiers), \
        f"Missing OWI identifier in: {new_record.identifiers}"

    # Verify OCLC in identifiers
    oclc_ids = [id.split('|')[0] for id in new_record.identifiers if id.endswith('|oclc')]
    assert len(oclc_ids) > 0, f"No OCLC numbers found in: {new_record.identifiers}"

    initial_catalog_count = db_manager.session.query(Record).filter(Record.source == 'oclcCatalog').count()

    catalog_process = CatalogProcess(
        'catalog_test',
        None,
        datetime.now(timezone.utc) - timedelta(minutes=2),
        None
    )

    catalog_process.runProcess()

    final_catalog_count = db_manager.session.query(Record).filter(Record.source == 'oclcCatalog').count()

    assert final_catalog_count > initial_catalog_count, (
        f"Catalog records didn't increase. Before: {initial_catalog_count}, After: {final_catalog_count}"
    )

    new_catalog_records = db_manager.session.query(Record).filter(
        Record.source == 'oclcCatalog',
        Record.date_created >= datetime.now(timezone.utc) - timedelta(minutes=1)
    ).all()

    matching_records = [
        record for record in new_catalog_records
        if any(oclc_id in record.identifiers for oclc_id in oclc_identifiers)
    ]
    
    assert len(matching_records) > 0, (
        f"No catalog records matched OCLC identifiers: {oclc_identifiers}"
    )

    db_manager.session.close()
