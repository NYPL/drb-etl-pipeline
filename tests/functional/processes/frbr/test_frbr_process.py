from processes import ClassifyProcess, CatalogProcess
from managers import RedisManager
from model import Record


def test_frbr_process(db_manager, unfrbrized_record_uuid):
    redis_manager = RedisManager()

    redis_manager.createRedisClient()
    redis_manager.clear_cache()

    classify_process = ClassifyProcess(None, None, None, unfrbrized_record_uuid)

    classify_process.runProcess()

    frbrized_record = db_manager.session.query(Record).filter(Record.uuid == unfrbrized_record_uuid).first()
    
    assert frbrized_record.frbr_status == 'complete'

    classify_record = (
        db_manager.session.query(Record)
            .filter(
                Record.source == 'oclcClassify',
                Record.title.ilike(f"%{frbrized_record.title}%"))
            .order_by(Record.date_created.desc())
            .first()
    )
    
    assert classify_record is not None

    oclc_identifiers = [id for id in classify_record.identifiers if id.endswith('|oclc')]
    
    catalog_process = CatalogProcess(None, None, None, None)
    catalog_process.runProcess(max_attempts=1)

    catalog_records = (
        db_manager.session.query(Record)
            .filter(
                Record.source == 'oclcCatalog',
                Record.source_id.in_(oclc_identifiers)
            )
            .all()
    )
    
    assert len(catalog_records) == len(oclc_identifiers)
