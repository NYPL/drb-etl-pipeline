from mappings.muse import MUSEMapping
from model import Source
from pymarc import MARCReader

def test_map_muse_record():
    with open('tests/fixtures/test-muse.mrc') as f:
        marc_reader = MARCReader(f)

        for record in marc_reader:
            if record is None:
                continue
            
            parsed_record = MUSEMapping(record)

            for attr in dir(parsed_record):
                print("parsed_record.%s = %r" % (attr, getattr(parsed_record, attr)))

            assert parsed_record.source == Source.MUSE.value
            assert parsed_record.source_id == '42'