from processes import DOABProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_doab_process():
    doab_process = DOABProcess('complete', None, None, None, 5, None)

    doab_process.runProcess()

    assert_ingested_records(source_name='doab')
