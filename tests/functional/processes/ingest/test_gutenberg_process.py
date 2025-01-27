from processes import GutenbergProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests

def test_gutenberg_process():
    gutenberg_process = GutenbergProcess('complete', None, None, None, 5, None)

    gutenberg_process.runProcess()

    records = assert_ingested_records(source_name='gutenberg')
    assert_uploaded_manifests(records)
