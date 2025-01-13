from processes import LOCProcess
from .assert_ingested_records import assert_ingested_records


def test_met_process():
    met_process = LOCProcess('complete', None, None, None, 5, None)

    met_process.runProcess()

    assert_ingested_records(source_name='loc')
