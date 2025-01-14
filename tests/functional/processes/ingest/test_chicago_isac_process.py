from processes import ChicagoISACProcess
from .assert_ingested_records import assert_ingested_records


def test_chigaco_isac_process():
    isac_process = ChicagoISACProcess('complete', None, None, None, 5, None)

    isac_process.runProcess()

    assert_ingested_records(source_name='isac')
