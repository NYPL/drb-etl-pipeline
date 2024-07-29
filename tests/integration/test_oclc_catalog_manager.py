import pytest
from loadEnv import loadEnvFile
from managers import OCLCCatalogManager

class TestOCLCCatalogManager:
    @pytest.fixture
    def testInstance(self):
        loadEnvFile('local-compose', fileString='config/local-compose.yaml')
        return OCLCCatalogManager()

    def testOCLCv2Search(self, testInstance):
        assert testInstance.queryBriefBibs('ti:The Waves')['numberOfRecords'] > 1000
