import pytest
from load_env import load_env_file
from managers import OCLCCatalogManager

class TestOCLCCatalogManager:
    @pytest.fixture
    def test_instance(self):
        load_env_file('local-compose', file_string='config/local-compose.yaml')
        return OCLCCatalogManager()

    def test_query_brief_bibs(self, test_instance: OCLCCatalogManager):
        assert test_instance.query_brief_bibs('ti:The Waves')['numberOfRecords'] > 1000

    def test_query_bibs(self, test_instance: OCLCCatalogManager):
        assert test_instance.query_bibs('ti:The Waves')['numberOfRecords'] > 1000

    def test_query_other_editions(self, test_instance: OCLCCatalogManager):
        assert test_instance.get_related_oclc_numbers(1) is not None

