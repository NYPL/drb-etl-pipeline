from processes import LOCProcess
from .assert_ingested_records import assert_ingested_records


def test_loc_process():
    loc_process = LOCProcess('complete', None, None, None, 5, None)

    loc_process.runProcess()

    assert_ingested_records(source_name='loc')
