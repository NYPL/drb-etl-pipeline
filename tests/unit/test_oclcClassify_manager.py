import pytest

from managers import ClassifyManager


class TestClassifyManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mockClean = mocker.patch.object(ClassifyManager, 'cleanStr')
        mockClean.side_effect = ['testTitle', 'testAuthor']
        return ClassifyManager(iden=1, idenType='test', title='testTitle', author='testAuthor')

    @pytest.fixture
    def mockGenerators(self, mocker):
        return mocker.patch.multiple(
            ClassifyManager,
            generateIdentifierURL=mocker.DEFAULT,
            generateAuthorTitleURL=mocker.DEFAULT
        )

    def test_initializer(self, testInstance):
        assert testInstance.identifier == 1
        assert testInstance.identifierType == 'test'
        assert testInstance.title == 'testTitle'
        assert testInstance.author == 'testAuthor'
        assert testInstance.start == 0

    def test_getClassifyResponse(self, testInstance, mocker):
        mockMethods = mocker.patch.multiple(
            ClassifyManager,
            generateQueryURL=mocker.DEFAULT,
            execQuery=mocker.DEFAULT,
            parseXMLResponse=mocker.DEFAULT
        )

        mockMethods['parseXMLResponse'].return_value = 'testXMLResponse'

        testClassifyResponse = testInstance.getClassifyResponse()

        assert testClassifyResponse == 'testXMLResponse'
        for _, method in mockMethods.items():
            method.assert_called_once
    
    def test_generateQueryURL_w_identifier(self, testInstance, mockGenerators):
        testInstance.generateQueryURL()

        mockGenerators['generateIdentifierURL'].assert_called_once
        mockGenerators['generateAuthorTitleURL'].assert_not_called
    
    def test_generateQueryURL_wo_identifier(self, testInstance, mockGenerators):
        testInstance.identifier = None
        testInstance.generateQueryURL()

        mockGenerators['generateIdentifierURL'].assert_not_called
        mockGenerators['generateAuthorTitleURL'].assert_called_once
    
    def test_generateQueryURL_wo_query_options(self, testInstance, mockGenerators):
        testInstance.identifier = None
        testInstance.title = None
        testInstance.generateQueryURL()

        mockGenerators['generateIdentifierURL'].assert_not_called
        mockGenerators['generateAuthorTitleURL'].assert_not_called

    def test_cleanStr(self):
        assert ClassifyManager.cleanStr('hello\n line\r') == 'hello line'

    def test_generateAuthorTitleURL(self, testInstance, mocker):
        mockAddOptions = mocker.patch.object(ClassifyManager, 'addClassifyOptions')

        testInstance.generateAuthorTitleURL()

        assert testInstance.query == 'http://classify.oclc.org/classify2/Classify?title=testTitle&author=testAuthor'
        mockAddOptions.assert_called_once

    def test_generateIdentifierURL(self, testInstance, mocker):
        mockAddOptions = mocker.patch.object(ClassifyManager, 'addClassifyOptions')

        testInstance.generateIdentifierURL()

        assert testInstance.query == 'http://classify.oclc.org/classify2/Classify?test=1'
        mockAddOptions.assert_called_once

    def test_addClassifyOptions(self, testInstance):
        testInstance.query = 'testQueryRoot'

        testInstance.addClassifyOptions()

        assert testInstance.query == 'testQueryRoot&summary=false&startRec=0&maxRecs=500'

    def test_execQuery_success(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcClassify.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 200
        mockResponse.text = 'testXMLResponse'

        testInstance.query = 'testQuery'
        testInstance.execQuery()

        assert testInstance.rawXML == 'testXMLResponse'
        mockRequest.get.assert_called_once_with('testQuery')

    def test_execQuery_error(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcClassify.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 500

        with pytest.raises(Exception):
            testInstance.query = 'testQuery'
            testInstance.execQuery()
