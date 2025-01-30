import pytest
import os
from processes import LOCProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests

@pytest.mark.skipif(
    os.getenv('IS_CI') == 'true',
    reason="Skipping in CI environment"
)

def test_loc_process():
    loc_process = LOCProcess('complete', None, None, None, 5, None)

    loc_process.runProcess()

    records = assert_ingested_records(source_name='loc')
    assert_uploaded_manifests(records)
