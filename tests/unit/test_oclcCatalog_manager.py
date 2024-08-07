import pytest
from requests.exceptions import ConnectionError, Timeout

from managers import OCLCCatalogManager


class TestOCLCCatalogManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {'OCLC_API_KEY': 'test_api_key'})

        return OCLCCatalogManager()

    def test_initializer(self, testInstance):
        assert testInstance.oclcKey == 'test_api_key'
        assert testInstance.attempts == 0

    def test_query_catalog_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclc_catalog.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.query_catalog(1)

        assert testResponse == 'testClassifyRecord'
        mockRequest.get.assert_called_once_with(
            'http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key',
            timeout=3
        )

    def test_query_catalog_error(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclc_catalog.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 500
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.query_catalog(1)

        assert testResponse == None
        mockRequest.get.assert_called_once_with(
            'http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key',
            timeout=3
        )

    def test_query_catalog_single_retry_then_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclc_catalog.requests')
        mockRequest.get.side_effect = [ConnectionError, mockResponse]

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.query_catalog(1)

        assert testResponse == 'testClassifyRecord'
        mockRequest.get.assert_has_calls(
            [mocker.call('http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key', timeout=3)] * 2
        )

    def test_query_catalog_exhaust_retries(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclc_catalog.requests')
        mockRequest.get.side_effect = [ConnectionError, ConnectionError, Timeout]

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.query_catalog(1)

        assert testResponse == None
        mockRequest.get.assert_has_calls(
            [mocker.call('http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key', timeout=3)] * 3
        )
