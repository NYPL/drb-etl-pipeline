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

    ## TODO:
    # 1. assert there is at least 1 record where the source is oclcClassify updated in the last minute
    # 2. run the catalog process
    # 3. assert there is at least 1 record where the source is oclcCatalog updated in the last minute
