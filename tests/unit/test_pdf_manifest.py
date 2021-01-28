import json
import pytest

from tests.helper import TestHelpers
from managers import PDFManifest

class TestPDFManifest:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testManifest(self):
        return PDFManifest('testSource', 'testMediaType')

    def test_initializer(self, testManifest):
        assert testManifest.metadata == {'@type': 'https://schema.org/Book'}
        assert testManifest.links == {
            'self': {},
            'alternate': [{'href': 'testSource', 'type': 'testMediaType'}]
        }
        assert testManifest.components == []
        assert testManifest.tableOfContents == []
        assert testManifest.openSection is None

    def test_addMetadata(self, testManifest, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.title = 'Test Record'
        mockRecord.authors = ['Author 1|||true', 'Author 2|||false']
        mockRecord.identifiers = ['id1|test', 'id2|isbn']

        testManifest.addMetadata(mockRecord)

        assert testManifest.metadata == {
            '@type': 'https://schema.org/Book', 'title': 'Test Record',
            'author': 'Author 1', 'identifier': 'urn:isbn:id2'
        }

    def test_addSection_no_existing(self, testManifest):
        testManifest.addSection('New Section', 'sectionURL')

        assert testManifest.openSection == {
            'href': 'sectionURL', 'title': 'New Section', 'children': []
        }

    def test_addSection_existing(self, testManifest):
        section1 = {
            'href': 'sectionURL_1', 'title': 'Section 1', 'children': []
        }
        testManifest.openSection = section1

        testManifest.addSection('Section 2', 'sectionURL_2')

        assert testManifest.tableOfContents[0] == section1
        assert testManifest.openSection == {
            'href': 'sectionURL_2', 'title': 'Section 2', 'children': []
        }

    def test_closeSection(self, testManifest):
        testSection = {
            'href': 'sectionURL', 'title': 'Test Section', 'children': []
        }
        testManifest.openSection = testSection

        testManifest.closeSection()

        assert testManifest.openSection is None
        assert testManifest.tableOfContents[0] == testSection

    def test_addChapter_direct_no_subsections(self, testManifest, mocker):
        mockChapter = mocker.MagicMock()
        mockManager = mocker.patch('managers.pdfManifest.PDFChapter')
        mockManager.return_value = mockChapter

        testManifest.addChapter('testLink', 'testTitle', '1-5')

        mockManager.assert_called_once_with('testLink', 'testTitle', '1-5')
        mockChapter.parsepageRange.assert_called_once
        assert testManifest.tableOfContents[0] == {'href': 'testLink', 'title': 'testTitle', 'pages': '1-5'}
        assert testManifest.components[0] == mockChapter

    def test_addChapter_parent_section_no_subsections(self, testManifest, mocker):
        mockChapter = mocker.MagicMock()
        mockManager = mocker.patch('managers.pdfManifest.PDFChapter')
        mockManager.return_value = mockChapter

        testManifest.openSection = {
            'href': 'testSection', 'title': 'Section 1', 'children': []
        }

        testManifest.addChapter('testLink', 'testTitle', '1-5')

        mockManager.assert_called_once_with('testLink', 'testTitle', '1-5')
        mockChapter.parsepageRange.assert_called_once
        assert testManifest.openSection['children'][0] == {'href': 'testLink', 'title': 'testTitle', 'pages': '1-5'}
        assert testManifest.components[0] == mockChapter

    def test_addChapter_direct_w_subsections(self, testManifest, mocker):
        mockChapter = mocker.MagicMock()
        mockManager = mocker.patch('managers.pdfManifest.PDFChapter')
        mockManager.return_value = mockChapter

        testManifest.addChapter('testLink', 'testTitle', '1-5', subsections=[1, 2, 3])
        mockManager.assert_called_once_with('testLink', 'testTitle', '1-5')
        mockChapter.parsepageRange.assert_called_once
        assert testManifest.tableOfContents[0] == {
            'href': 'testLink', 'title': 'testTitle', 'pages': '1-5', 'children': [1, 2, 3]
        }
        assert testManifest.components[0] == mockChapter

    def test_toDict(self, testManifest):
        assert testManifest.toDict() == {
            'context': 'https://test_aws_bucket-s3.amazonaws.com/manifests/context.jsonld',
            'media_type': 'application/pdf+json',
            'metadata': {'@type': 'https://schema.org/Book'},
            'links': {'self': {}, 'alternate': [{'href': 'testSource', 'type': 'testMediaType'}]},
            'components': [],
            'table_of_contents': []
        }

    def test_toJson(self, testManifest):
        jsonManifest = testManifest.toJson()
        assert isinstance(jsonManifest, str)
        assert json.loads(jsonManifest)['context'] == 'https://test_aws_bucket-s3.amazonaws.com/manifests/context.jsonld'
