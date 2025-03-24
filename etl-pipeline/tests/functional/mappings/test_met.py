import json

from mappings.met import METMapping
from model import Source


def test_map_met_record():
    with open('tests/fixtures/test-met.json') as f:
        met_record = json.load(f)

        parsed_record = METMapping(source=met_record).record

        assert parsed_record.source == Source.MET.value
        assert parsed_record.source_id == '2235|met'
        assert parsed_record.title == 'Constitution and by-laws, 1870'
