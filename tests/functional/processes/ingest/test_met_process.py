import pytest
import os
from processes import METProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests

@pytest.mark.skipif(
    os.getenv('IS_CI') == 'true',
    reason="Skipping in CI environment"
)
def test_met_process():
    met_process = METProcess('complete', None, None, None, 5, None)

    met_process.runProcess()
    
    records = assert_ingested_records(source_name='met')
    assert_uploaded_manifests(records)
