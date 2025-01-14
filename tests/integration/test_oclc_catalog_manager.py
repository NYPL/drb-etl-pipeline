import pytest
from managers import OCLCCatalogManager

class TestOCLCCatalogManager:
    @pytest.fixture
    def test_instance(self):
        return OCLCCatalogManager()

    def test_query_bibs(self, test_instance: OCLCCatalogManager):
        bibs = test_instance.query_bibs('ti:The Waves')

        assert len(bibs) > 0

    def test_query_other_editions(self, test_instance: OCLCCatalogManager):
        related_oclc_numbers = test_instance.get_related_oclc_numbers(1)
        
        assert len(related_oclc_numbers) > 0
        assert 1 not in set(related_oclc_numbers)
