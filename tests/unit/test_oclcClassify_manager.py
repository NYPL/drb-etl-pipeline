from lxml import etree
import pytest
import os

from managers.oclcClassify import ClassifyManager, ClassifyError


class TestClassifyManager:
    @pytest.fixture
    def testInstance(self, mocker):
        mockClean = mocker.patch.object(ClassifyManager, 'cleanStr')
        mockClean.side_effect = ['testTitle', 'testAuthor', 'testTitle', 'testAuthor']
        return ClassifyManager(iden=1, idenType='test', title='testTitle', author='testAuthor')

    @pytest.fixture
    def mockGenerators(self, mocker):
        return mocker.patch.multiple(
            ClassifyManager,
            generateIdentifierURL=mocker.DEFAULT,
            generateAuthorTitleURL=mocker.DEFAULT
        )

    @pytest.fixture
    def testXMLResponse(self):
        def constructResponse(code, responseBlock):
            return etree.tostring(etree.XML('''<?xml version="1.0"?>
                <classify xmlns="http://classify.oclc.org" xmlns:oclc="http://classify.oclc.org">
                    <response code="{}"/>
                    {}
                </classify>
            '''.format(code, responseBlock))).decode('utf-8')
        
        return constructResponse

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
    
    def test_generateQueryURL_wo_query_options(self, testInstance):
        testInstance.identifier = None
        testInstance.title = None

        with pytest.raises(ClassifyError):
            testInstance.generateQueryURL()

    def test_cleanStr(self):
        assert ClassifyManager.cleanStr('hello\n line\r') == 'hello line'

    def test_generateAuthorTitleURL(self, testInstance, mocker):
        mockAddOptions = mocker.patch.object(ClassifyManager, 'addClassifyOptions')

        testInstance.generateAuthorTitleURL()

        assert testInstance.query == 'https://metadata.api.oclc.org/classify?title=testTitle&author=testAuthor'
        mockAddOptions.assert_called_once

    def test_generateIdentifierURL(self, testInstance, mocker):
        mockAddOptions = mocker.patch.object(ClassifyManager, 'addClassifyOptions')

        testInstance.generateIdentifierURL()

        assert testInstance.query == 'https://metadata.api.oclc.org/classify?test=1'
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
        mockRequest.get.assert_called_once_with('testQuery', headers={'X-OCLC-API-Key': os.environ['OCLC_CLASSIFY_API_KEY']}, timeout=10)

    def test_execQuery_error(self, testInstance, mocker):
        mockResponse = mocker.MagicMock()
        mockRequest = mocker.patch('managers.oclcClassify.requests')
        mockRequest.get.return_value = mockResponse

        mockResponse.status_code = 500
        mockResponse.raise_for_status.side_effect = Exception

        with pytest.raises(Exception):
            testInstance.query = 'testQuery'
            testInstance.execQuery()

    def test_parseXMLResponse_status_102(self, testInstance, testXMLResponse):
        testInstance.rawXML = testXMLResponse(102, '<data/>')

        with pytest.raises(ClassifyError):
            testInstance.parseXMLResponse()

    def test_parseXMLResponse_status_200(self, testInstance, testXMLResponse):
        testInstance.rawXML = testXMLResponse(200, '<data/>')

        with pytest.raises(ClassifyError):
            testInstance.parseXMLResponse()

    def test_parseXMLResponse_status_101(self, testInstance, testXMLResponse, mocker):
        testInstance.rawXML = testXMLResponse(101, '<data/>')
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            cleanIdentifier=mocker.DEFAULT,
            getClassifyResponse=mocker.DEFAULT
        )
        classifyMocks['cleanIdentifier'].return_value = 'idV2'
        classifyMocks['getClassifyResponse'].return_value = 'cleanedIdentifierResponse'

        testResponse = testInstance.parseXMLResponse()

        assert testResponse == 'cleanedIdentifierResponse'
        classifyMocks['cleanIdentifier'].assert_called_once_with(1)
        classifyMocks['getClassifyResponse'].assert_called_once

    def test_parseXMLResponse_status_101_invalid(self, testInstance, testXMLResponse, mocker):
        testInstance.rawXML = testXMLResponse(101, '<data/>')
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            cleanIdentifier=mocker.DEFAULT,
            getClassifyResponse=mocker.DEFAULT
        )
        classifyMocks['cleanIdentifier'].return_value = 1
        classifyMocks['getClassifyResponse'].return_value = 'cleanedIdentifierResponse'

        with pytest.raises(ClassifyError):
            testInstance.parseXMLResponse()

    def test_parseXMLResponse_status_2(self, testInstance, testXMLResponse, mocker):
        testInstance.rawXML = testXMLResponse(2, '<data id="test"/>')

        testXML = testInstance.parseXMLResponse()[0]

        assert testXML.find('.//response', namespaces=ClassifyManager.NAMESPACE).get('code') == '2'
        assert testXML.find('.//data', namespaces=ClassifyManager.NAMESPACE).get('id') == 'test'

    def test_parseXMLResponse_status_4(self, testInstance, testXMLResponse, mocker):
        workXML = '''
            <works>
                <work wi="123" title="test123"/>
                <work wi="456" title="test456"/>
            </works>
        '''
        testInstance.rawXML = testXMLResponse(4, workXML)
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            checkTitle=mocker.DEFAULT,
            getClassifyResponse=mocker.DEFAULT
        )
        classifyMocks['checkTitle'].side_effect = [False, True]
        classifyMocks['getClassifyResponse'].return_value = ['multiWorkResponse']

        testResponse = testInstance.parseXMLResponse()

        assert testResponse == ['multiWorkResponse']
        classifyMocks['checkTitle'].assert_has_calls([
            mocker.call('test123'), mocker.call('test456')
        ])
        classifyMocks['getClassifyResponse'].assert_called_once

    def test_parseXMLRepsonse_invalid_xml(self, testInstance, testXMLResponse, mocker):
        testInstance.rawXML = testXMLResponse(2, '<data/>')
        mockEtree = mocker.patch('managers.oclcClassify.etree')
        mockEtree.fromstring.side_effect = etree.ParserError

        with pytest.raises(ClassifyError):
            testInstance.parseXMLResponse()

    def test_checkAndFetchAdditionalEditions_true(self, testInstance, testXMLResponse, mocker):
        editionElements = ''.join('<oclc:edition>{}</oclc:edition>'.format(i) for i in range(501))
        xmlDoc = testXMLResponse(2, editionElements) 

        mockFetch = mocker.patch.object(ClassifyManager, 'fetchAdditionalIdentifiers')

        testInstance.checkAndFetchAdditionalEditions(etree.fromstring(xmlDoc.encode('utf-8')))

        mockFetch.assert_called_once()

    def test_checkAndFetchAdditionalEditions_false(self, testInstance, testXMLResponse, mocker):
        editionElements = ''.join('<oclc:edition>{}</oclc:edition>'.format(i) for i in range(100))
        xmlDoc = testXMLResponse(2, editionElements) 

        mockFetch = mocker.patch.object(ClassifyManager, 'fetchAdditionalIdentifiers')

        testInstance.checkAndFetchAdditionalEditions(etree.fromstring(xmlDoc.encode('utf-8')))

        mockFetch.assert_not_called()

    def test_fetchAdditionalIdentifiers(self, testInstance, mocker):
        mockXML = mocker.MagicMock()
        mockEtree = mocker.patch('managers.oclcClassify.etree')
        mockEtree.fromstring.return_value = mockXML

        mockXML.xpath.side_effect = [[i for i in range(25)], []]

        mockGenerate = mocker.patch.object(ClassifyManager, 'generateQueryURL')
        mockExecute = mocker.patch.object(ClassifyManager, 'execQuery')

        testInstance.rawXML = '<data>test</data>'
        testInstance.fetchAdditionalIdentifiers()

        assert testInstance.addlIds == ['{}|oclc'.format(i) for i in range(25)]
        mockGenerate.assert_has_calls([mocker.call(), mocker.call()])
        mockExecute.assert_has_calls([mocker.call(), mocker.call()])

    def test_checkTitle_lang_match_same(self, testInstance, mocker):
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            getStrLang=mocker.DEFAULT,
            cleanTitle=mocker.DEFAULT
        )

        classifyMocks['getStrLang'].side_effect = ['te', 'te']
        classifyMocks['cleanTitle'].side_effect = [['oclc', 'title'], ['test', 'title']]

        assert testInstance.checkTitle('oclcTitle') is True
        classifyMocks['getStrLang'].assert_has_calls([
            mocker.call('oclcTitle'), mocker.call('testTitle')
        ])
        classifyMocks['cleanTitle'].assert_has_calls([
            mocker.call('oclcTitle'), mocker.call('testTitle')
        ])

    def test_checkTitle_lang_match_different(self, testInstance, mocker):
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            getStrLang=mocker.DEFAULT,
            cleanTitle=mocker.DEFAULT
        )

        classifyMocks['getStrLang'].side_effect = ['te', 'te']
        classifyMocks['cleanTitle'].side_effect = [['oclc', 'collected'], ['test', 'title']]

        assert testInstance.checkTitle('oclcCollected') is False
        classifyMocks['getStrLang'].assert_has_calls([
            mocker.call('oclcCollected'), mocker.call('testTitle')
        ])
        classifyMocks['cleanTitle'].assert_has_calls([
            mocker.call('oclcCollected'), mocker.call('testTitle')
        ])

    def test_checkTitle_no_lang_match(self, testInstance, mocker):
        classifyMocks = mocker.patch.multiple(
            ClassifyManager,
            getStrLang=mocker.DEFAULT,
            cleanTitle=mocker.DEFAULT
        )

        classifyMocks['getStrLang'].side_effect = ['te', 'ot']

        assert testInstance.checkTitle('oclcLanguage') is True
        classifyMocks['getStrLang'].assert_has_calls([
            mocker.call('oclcLanguage'), mocker.call('testTitle')
        ])
        classifyMocks['cleanTitle'].assert_not_called

    def test_getStrLang_success(self):
        assert ClassifyManager.getStrLang('English') == 'en'

    def test_getStrLang_nonLatin(self):
        assert ClassifyManager.getStrLang('わかりません') == 'ja'

    def test_getStrLang_error(self):
        assert ClassifyManager.getStrLang('01234') == 'unk'

    def test_getStrLang_not_a_string_error(self):
        assert ClassifyManager.getStrLang(34) == 'unk'

    def test_cleanTitle(self):
        assert ClassifyManager.cleanTitle('The Real Title()') == ['real', 'title']

    def test_cleanIdentifier(self):
        assert ClassifyManager.cleanIdentifier('no1234') == '1234'

    def test_getQueryableIdentifiers(self):
        assert ClassifyManager.getQueryableIdentifiers(['1|isbn', '2|test']) == ['1|isbn']
