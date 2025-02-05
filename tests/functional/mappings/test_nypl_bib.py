from .nypl_source_data import TEST_NYPL_BIB
from mappings.nypl_bib import map_nypl_bib_to_record


def test_nypl_bib_mapping():
    map_nypl_bib_to_record(TEST_NYPL_BIB)
