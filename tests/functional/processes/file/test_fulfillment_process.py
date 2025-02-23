from processes import ClusterProcess, FulfillURLManifestProcess
from model import Record, Item
import json
import os
from sqlalchemy.orm import joinedload
import pytest

def test_fulfillment_process(db_manager, s3_manager, seed_test_data):

    limited_access_record_uuid = seed_test_data['manifest_record_uuid']

    cluster_process = ClusterProcess('complete', None, None, limited_access_record_uuid, None)
    cluster_process.runProcess()
    db_manager.session.commit()

    record = db_manager.session.query(Record).filter_by(uuid=limited_access_record_uuid).first()
    item = db_manager.session.query(Item)\
        .options(joinedload(Item.links))\
        .filter_by(record_id=record.id)\
        .first()

    assert item is not None, "Item not created by cluster process"
    
    epub_link = next((link for link in item.links if link.media_type == 'application/epub+zip'), None)
    assert epub_link is not None, "EPUB link not found in item links"

    test_manifest = {
        "links": [{"type": epub_link.media_type, "href": epub_link.url}],
        "readingOrder": [{"type": epub_link.media_type, "href": epub_link.url}],
        "resources": [{"type": epub_link.media_type, "href": epub_link.url}],
        "toc": [{"href": epub_link.url}]
    }
    
    s3_key = f"manifests/publisher_backlist/test_{limited_access_record_uuid}.json"
    s3_manager.s3Client.put_object(
        Bucket=os.environ['FILE_BUCKET'],
        Key=s3_key,
        Body=json.dumps(test_manifest),
        ContentType='application/json'
    )

    fulfill_process = FulfillURLManifestProcess(
        'complete',
        None,
        None,
        None
    )
    fulfill_process.runProcess()

    response = s3_manager.s3Client.get_object(Bucket=os.environ['FILE_BUCKET'], Key=s3_key)
    updated_manifest = json.loads(response['Body'].read().decode())

    expected_url = f"https://{os.environ['DRB_API_HOST']}/fulfill/{epub_link.id}"

    assert updated_manifest['readingOrder'][0]['href'] == expected_url, (
        f"Expected readingOrder URL: {expected_url}\n"
        f"Actual: {updated_manifest['readingOrder'][0]['href']}"
    )
    
    assert updated_manifest['resources'][0]['href'] == expected_url, (
        f"Expected resources URL: {expected_url}\n"
        f"Actual: {updated_manifest['resources'][0]['href']}"
    )
    
    assert updated_manifest['toc'][0]['href'] == expected_url, (
        f"Expected toc URL: {expected_url}\n"
        f"Actual: {updated_manifest['toc'][0]['href']}"
    )

    s3_manager.s3Client.delete_object(
        Bucket=os.environ['FILE_BUCKET'],
        Key=s3_key
    )
