from processes import MUSEProcess
from .assert_ingested_records import assert_ingested_records



def test_muse_process():
    muse_process = MUSEProcess('complete', None, None, None, 5, None)

    muse_process.runProcess()

    assert_ingested_records(source_name='muse')
