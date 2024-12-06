from processes import MUSEProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_muse_process():
    muse_process = MUSEProcess('complete', None, None, None, 5, None)

    muse_process.runProcess()

    assert_ingested_records(source_name='muse')
