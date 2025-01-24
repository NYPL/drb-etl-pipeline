from processes import DOABProcess
from .assert_ingested_records import assert_ingested_records


def test_doab_process():
    doab_process = DOABProcess('complete', None, None, None, 1, None)

    doab_process.runProcess()

    assert_ingested_records(source_name='doab')
