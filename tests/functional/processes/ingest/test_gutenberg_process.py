from processes import GutenbergProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_gutenberg_process():
    gutenberg_process = GutenbergProcess('complete', None, None, None, 5, None)

    gutenberg_process.runProcess()

    assert_ingested_records(source_name='gutenberg')
