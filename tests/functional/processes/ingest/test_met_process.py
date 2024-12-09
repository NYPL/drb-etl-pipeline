from processes import LOCProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_met_process():
    met_process = LOCProcess('complete', None, None, None, 5, None)

    met_process.runProcess()

    assert_ingested_records(source_name='loc')
