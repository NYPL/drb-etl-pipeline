from processes import PublisherBacklistProcess
from load_env import load_env_file
from .assert_ingested_records import assert_ingested_records

load_env_file('local', file_string='config/local.yaml')


def test_publisher_backlist_process():
    publisher_backlist_project = PublisherBacklistProcess('complete', None, None, None, 5, None)

    # TODO: pull from a list of potential sources
    # publisher_backlist_project.runProcess()

    # assert_ingested_records(source_name='UofM')
