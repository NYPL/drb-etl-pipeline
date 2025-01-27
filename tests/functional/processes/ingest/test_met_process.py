from model import Part
from processes import METProcess
from .assert_ingested_records import assert_ingested_records
from managers.s3 import S3Manager


def test_met_process():
    met_process = METProcess('complete', None, None, None, 5, None)

    met_process.runProcess()
    records = assert_ingested_records(source_name='met')
    
    s3_manager = S3Manager()
    s3_manager.createS3Client() 

    for record in records:
        parts= record.get_parts()

        manifest_part = next(part for part in parts if part.file_type == 'application/webpub+json')

        manifest_head_response = s3_manager.s3Client.head_object(Key=manifest_part.get_file_key(), Bucket=manifest_part.get_file_bucket())

        assert manifest_head_response is not None
