import pytest
import requests
from requests import ConnectionError

from managers import DOABLinkManager
from managers.doabParser import LinkError


class TestDOABLinkManager:
    @pytest.fixture
    def testManager(self, mocker):
        return DOABLinkManager(mocker.MagicMock())

    @pytest.fixture
    def testHasParts(self):
        return [
            '1|testURI|test|testType|{"test": true}',
            '2|testOtherURI|test|testOtherType|{"test": false}'
        ]

    def test_loadParsers(self, testManager):
        assert len(testManager.parsers) == 7
        assert testManager.parsers[0].__name__ == 'SpringerParser'
        assert testManager.parsers[6].__name__ == 'DefaultParser'

    def test_selectParser(self, testManager, mocker):
        mockFindURI = mocker.patch.object(DOABLinkManager, 'findFinalURI')
        mockFindURI.return_value = ('testRoot', 'testType')

        testManager.parsers = []
        parserInstances = []
        for i in range(3):
            mockInstance = mocker.MagicMock()
            mockInstance.validateURI.return_value = True if i == 1 else False

            mockParser = mocker.MagicMock()
            mockParser.return_value = mockInstance

            parserInstances.append(mockInstance)
            testManager.parsers.append(mockParser)

        testParser = testManager.selectParser('testURI', 'testType')

        assert testParser == parserInstances[1]
        for i in range(3):
            testManager.parsers[1].assert_called_once_with('testRoot', 'testType', testManager.record)
        parserInstances[2].validateURI.assert_not_called

    def test_parseLinks(self, testManager, testHasParts, mocker):
        testManager.record.has_part = testHasParts

        mockParser = mocker.MagicMock(uri='testSourceURI')
        mockParser.createLinks.return_value = [
            ('parseURI1', {'other': True}, 'testType1', 'testManifest', None),
            ('parseURI2', {'other': False}, 'testType2', None, 'testEPub')
        ]

        mockSelect = mocker.patch.object(DOABLinkManager, 'selectParser')
        mockSelect.side_effect = [mockParser] * 2

        testManager.parseLinks()

        assert testManager.record.has_part == [
            '1|parseURI1|test|testType1|{"test": true, "other": true}',
            '1|parseURI2|test|testType2|{"test": true, "other": false}'
        ]
        assert testManager.manifests == ['testManifest']
        assert testManager.ePubLinks == ['testEPub']

    def test_parseLinks_error(self, testManager, testHasParts, mocker):
        testManager.record.has_part = testHasParts

        mockSelect = mocker.patch.object(DOABLinkManager, 'selectParser')
        mockSelect.side_effect = [LinkError('test')] * 2

        testManager.parseLinks()

        assert testManager.record.has_part == []

    def test_findFinalURI_direct(self, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 200
        mockResponse.headers = {'Content-Type': 'text/html; utf-8'}

        mockHead = mocker.patch.object(requests, 'head')
        mockHead.return_value = mockResponse

        testURI, testType = DOABLinkManager.findFinalURI('testURI', 'testType')

        assert testURI == 'testURI'
        assert testType == 'text/html'
        mockHead.assert_called_once_with('testURI', allow_redirects=False, timeout=15)

    def test_findFinalURI_error(self, mocker):
        mockHead = mocker.patch.object(requests, 'head')
        mockHead.side_effect = ConnectionError

        with pytest.raises(LinkError):
            DOABLinkManager.findFinalURI('testURI', 'testType')

    def test_findFinalURI_redirect(self, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 301
        mockResponse.headers = {'Location': 'sourceURI'}

        mockResponse2 = mocker.MagicMock()
        mockResponse2.status_code = 200
        mockResponse2.headers = {'Content-Type': 'application/test'}

        mockHead = mocker.patch.object(requests, 'head')
        mockHead.side_effect = [mockResponse, mockResponse2]

        testURI, testType = DOABLinkManager.findFinalURI('testURI', 'testType')

        assert testURI == 'sourceURI'
        assert testType == 'application/test'
        mockHead.assert_has_calls([
            mocker.call('testURI', allow_redirects=False, timeout=15),
            mocker.call('sourceURI', allow_redirects=False, timeout=15)
        ])
