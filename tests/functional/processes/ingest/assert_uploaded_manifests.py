import pytest
import os
from model import Record
from managers.s3 import S3Manager

@pytest.mark.skipif(
    os.getenv('IS_CI') == 'true', 
    reason="Skipping in CI environment"
)

def assert_uploaded_manifests(records: list[Record]):
    s3_manager = S3Manager()
    s3_manager.createS3Client() 

    for record in records:
        parts = record.get_parts()

        manifest_part = next((part for part in parts if part.file_type == 'application/webpub+json'), None)

        if manifest_part and 'epubs' not in manifest_part.url:
            manifest_head_response = s3_manager.s3Client.head_object(Key=manifest_part.get_file_key(), Bucket=manifest_part.get_file_bucket())

            assert manifest_head_response is not None
