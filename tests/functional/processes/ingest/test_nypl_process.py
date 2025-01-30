import pytest
import os
from processes import NYPLProcess
from .assert_ingested_records import assert_ingested_records

@pytest.mark.skipif(
    os.getenv('IS_CI') == 'true',
    reason="Skipping in CI environment"
)

def test_nypl_process():
    nypl_process = NYPLProcess('daily', None, None, None, 5, None)

    nypl_process.runProcess()

    assert_ingested_records(source_name='nypl')
