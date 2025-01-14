from processes import GutenbergProcess
from .assert_ingested_records import assert_ingested_records


def test_gutenberg_process():
    gutenberg_process = GutenbergProcess('complete', None, None, None, 5, None)

    gutenberg_process.runProcess()

    assert_ingested_records(source_name='gutenberg')
