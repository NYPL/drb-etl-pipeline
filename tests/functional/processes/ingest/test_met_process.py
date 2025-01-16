from processes import METProcess
from .assert_ingested_records import assert_ingested_records


def test_met_process():
    met_process = METProcess('complete', None, None, None, 5, None)

    met_process.runProcess()

    records = assert_ingested_records(source_name='met')

    # assert that for each record there exists a PDF manifest in S3
    
    # run the S3 process

    # assert that for each record, we have saved the PDF in S3

