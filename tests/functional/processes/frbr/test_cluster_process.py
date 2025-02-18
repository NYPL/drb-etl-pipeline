from processes import ClusterProcess
from model import Record, Item, Edition, Work

def test_cluster_process(db_manager, unclustered_record_uuid):
    cluster_process = ClusterProcess('complete', None, None, unclustered_record_uuid, None)

    unclustered_record = db_manager.session.query(Record).filter(Record.uuid == unclustered_record_uuid).first()

    assert unclustered_record.cluster_status == False

    cluster_process.runProcess()
    
    db_manager.session.commit()

    clustered_record = db_manager.session.query(Record).filter(Record.uuid == unclustered_record_uuid).first()

    assert clustered_record.cluster_status == True
    
    frbrized_model = (
        db_manager.session.query(Item, Edition, Work)
            .join(Edition, Edition.id == Item.edition_id)
            .join(Work, Work.id == Edition.work_id)
            .filter(Item.record_id == clustered_record.id)
            .first()
    )

    item, edition, work = frbrized_model

    assert item is not None
    assert edition is not None
    assert work is not None
    