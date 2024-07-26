import pytest
from main import loadEnvFile
from managers import OCLCCatalogManager

class TestOCLCCatalogManager:
    @pytest.fixture
    def testInstance(self):
        loadEnvFile('sample-compose', fileString='config/local.yaml')
        # TODO: In the future the catalog manager shouldn't take the OCLC no
        return OCLCCatalogManager(1)

    def testOCLCv2Auth(self, testInstance):
        testInstance.getToken()
        assert len(testInstance.token) > 10
        assert testInstance.tokenExpiresAt is not None

    def testOCLCv2Search(self, testInstance):
        assert testInstance.queryBriefBibs('ti:The Waves')['numberOfRecords'] > 1000