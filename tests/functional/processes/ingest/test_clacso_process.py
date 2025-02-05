from processes import CLACSOProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests


def test_clacso_process():
    clacso_process = CLACSOProcess('complete', None, None, None, 5, None)

    clacso_process.runProcess()

    #records = assert_ingested_records(source_name='clacso')
    #assert_uploaded_manifests(records)
