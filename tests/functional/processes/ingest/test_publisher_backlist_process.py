import pytest
import os
from processes import PublisherBacklistProcess
from .assert_ingested_records import assert_ingested_records

def test_publisher_backlist_process():
    publisher_backlist_project = PublisherBacklistProcess('complete', None, None, None, 5, None)

    # TODO: pull from a list of potential sources
    # publisher_backlist_project.runProcess()

    # assert_ingested_records(source_name='UofM')
