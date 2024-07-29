import pytest
from loadEnv import loadEnvFile
from managers import OCLCCatalogManager

class TestOCLCCatalogManager:
    @pytest.fixture
    def testInstance(self):
        loadEnvFile('local-compose', fileString='config/local-compose.yaml')
        # TODO: In the future the catalog manager shouldn't take the OCLC no
        return OCLCCatalogManager(1)

    def testOCLCv2Search(self, testInstance):
        assert testInstance.queryBriefBibs('ti:The Waves')['numberOfRecords'] > 1000
