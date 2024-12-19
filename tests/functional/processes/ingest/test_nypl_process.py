from processes import NYPLProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_nypl_process():
    nypl_process = NYPLProcess('complete', None, None, None, 5, None)

    nypl_process.runProcess()

    assert_ingested_records(source_name='nypl')
