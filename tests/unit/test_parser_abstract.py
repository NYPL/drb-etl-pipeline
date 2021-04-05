import pytest

from managers.parsers.abstractParser import AbstractParser
from tests.helper import TestHelpers


class TestAbstractParser:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testParser(self, mocker):
        class TestParser(AbstractParser):
            def __init__(self, uri, mediaType, record):
                super().__init__(uri, mediaType, record)

            def validateURI(self):
                return super().validateURI()
            
            def createLinks(self):
                return super().createLinks()

            def generateManifest(self, sourceURI, manifestURI):
                return super().generateManifest(sourceURI, manifestURI)

            def generateS3Root(self):
                return super().generateS3Root()
        
        return TestParser('testURI', 'testType', mocker.MagicMock(title='testRecord'))

    def test_uriSetter(self, testParser):
        assert testParser.uri == 'http://testURI'

        testParser.uri = 'https://newURI'

        assert testParser.uri == 'https://newURI'

    def test_validateURI(self, testParser):
        assert testParser.validateURI() is True

    def test_createLinks(self, testParser):
        assert testParser.createLinks() == [('http://testURI', None ,'testType', None, None)]

    def test_generateManifest(self, testParser, mocker):
        mockManifest = mocker.MagicMock(links={})
        mockManifest.toJson.return_value = 'jsonManifest'

        mockManifestManager = mocker.patch('managers.parsers.abstractParser.WebpubManifest')
        mockManifestManager.return_value = mockManifest

        testManifest = testParser.generateManifest('sourceURI', 'manifestURI')

        assert testManifest == 'jsonManifest'
        assert mockManifest.links == {'self': {'href': 'manifestURI', 'type': 'application/webpub+json'}}
        mockManifestManager.assert_called_once_with('sourceURI', 'application/pdf')
        mockManifest.addMetadata.assert_called_once_with(testParser.record)
        mockManifest.addChapter.assert_called_once_with('sourceURI', 'testRecord')
        mockManifest.toJson.assert_called_once()

    def test_generateS3Root(self, testParser):
        assert testParser.generateS3Root() == 'https://test_aws_bucket.s3.amazonaws.com/'

