import pytest
import os
from processes import ChicagoISACProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests

def test_chigaco_isac_process():
    isac_process = ChicagoISACProcess('complete', None, None, None, 5, None)

    isac_process.runProcess()

    records = assert_ingested_records(source_name='isac')
    assert_uploaded_manifests(records)
