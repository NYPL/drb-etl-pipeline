import pytest
from requests.exceptions import ConnectionError, Timeout

from managers import OCLCCatalogManager


class TestOCLCCatalogManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mocker.patch.dict('os.environ', {'OCLC_API_KEY': 'test_api_key'})

        return OCLCCatalogManager(1)

    def test_initializer(self, testInstance):
        assert testInstance.oclcNo == 1
        assert testInstance.oclcKey == 'test_api_key'
        assert testInstance.attempts == 0

    def test_queryCatalog_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcCatalog.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.queryCatalog()

        assert testResponse == 'testClassifyRecord'
        mockRequest.get.assert_called_once_with(
            'http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key',
            timeout=3
        )

    def test_queryCatalog_error(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcCatalog.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 500
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.queryCatalog()

        assert testResponse == None
        mockRequest.get.assert_called_once_with(
            'http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key',
            timeout=3
        )

    def test_queryCatalog_single_retry_then_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcCatalog.requests')
        mockRequest.get.side_effect = [ConnectionError, mockResponse]

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.queryCatalog()

        assert testResponse == 'testClassifyRecord'
        mockRequest.get.assert_has_calls(
            [mocker.call('http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key', timeout=3)] * 2
        )

    def test_queryCatalog_exhaust_retries(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcCatalog.requests')
        mockRequest.get.side_effect = [ConnectionError, ConnectionError, Timeout]

        mockResponse.status_code = 200
        mockResponse.text = 'testClassifyRecord'

        testResponse = testInstance.queryCatalog()

        assert testResponse == None
        mockRequest.get.assert_has_calls(
            [mocker.call('http://www.worldcat.org/webservices/catalog/content/1?wskey=test_api_key', timeout=3)] * 3
        )
