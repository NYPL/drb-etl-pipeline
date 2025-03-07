from processes import HathiTrustProcess
from .assert_ingested_records import assert_ingested_records


def test_hathi_trust_process():
    hathi_trust_process = HathiTrustProcess('daily', None, None, None, 5, None)

    number_of_records_ingested = hathi_trust_process.runProcess()

    assert_ingested_records(source_name='hathitrust', expected_number_of_records=number_of_records_ingested)
