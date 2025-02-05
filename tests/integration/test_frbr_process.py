import pytest
from model import Record
from processes import ClassifyProcess

@pytest.mark.integration
def test_classify_process_updates_frbr_status(db_manager, seed_oclc_test_data):
    test_source_id = seed_oclc_test_data['source_id'][0]
    pre_record = db_manager.session.query(Record).filter(
        Record.source_id.contains([test_source_id])
    ).first()
    
    assert pre_record is not None, "Test record not found in database"
    assert pre_record.frbr_status == 'to_do'
    
    classify_process = ClassifyProcess('complete', None, None, None)
    classify_process.runProcess()
    
    post_record = db_manager.session.query(Record).filter(
        Record.source_id.contains([test_source_id])
    ).first()
    
    assert post_record.frbr_status == 'complete'
