from model import Source
from processes import ChicagoISACProcess
from .assert_ingested_records import assert_ingested_records
from .assert_uploaded_manifests import assert_uploaded_manifests


def test_chicago_isac_process():
    isac_process = ChicagoISACProcess('complete', None, None, None, 5, None)

    number_of_records_ingested = isac_process.runProcess()

    records = assert_ingested_records(source_name=Source.CHICACO_ISAC.value, expected_number_of_records=number_of_records_ingested)
    assert_uploaded_manifests(records)
