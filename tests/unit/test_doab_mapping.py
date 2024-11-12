import pytest

from mappings.doab import DOABMapping
from mappings.base_mapping import MappingError


class TestDOABMapping:
    @pytest.fixture
    def testRecord(self, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.identifiers = ['1|doab', '2|TEST', 'http://doabooks.org/handle/00.00.00/0000|doi', 'http://test|doab']
        mockRecord.title = 'Main Title'
        mockRecord.subjects = ['subj1', 'subj2', 'subj3', 'bic subj4']
        mockRecord.has_part = ['1|http://testURL|muse|testType|testFlags', '2|testID|muse|test|test']
        mockRecord.languages = ['||lang1', '||lang2']
        mockRecord.contributors = ['cont1||', 'cont2||']
        mockRecord.rights = ['doab| license ||statement|', 'doab|||otherStmt|']

        return mockRecord

    @pytest.fixture
    def testMapping(self, testRecord):
        class TestMapping(DOABMapping):
            def __init__(self):
                self.mapping = None
                self.record = testRecord
        
        return TestMapping()

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'identifiers', 'authors', 'contributors', 'title', 'is_part_of',
            'publisher', 'spatial', 'dates', 'languages', 'extent', 'abstract',
            'subjects', 'has_part', 'rights'
        ]
        assert recordMapping['is_part_of'] == [('./dc:relation/text()', '{0}||series')]

    def test_applyFormatting(self, testMapping, mocker):
        mocker.patch.multiple(DOABMapping,
            parseIdentifiers=mocker.MagicMock(return_value=['testID']),
            parseRights=mocker.MagicMock(return_value='testRights'),
            parseLinks=mocker.MagicMock(return_value='testLinks')
        )

        testMapping.source_id = 'testID'
        testMapping.applyFormatting()

        assert testMapping.record.source == 'doab'
        assert testMapping.record.title == 'Main Title'
        assert testMapping.record.subjects == ['subj1', 'subj2', 'subj3']
        assert testMapping.record.identifiers == ['testID']
        assert testMapping.record.rights == 'testRights'
        assert testMapping.record.has_part == 'testLinks'

    def test_applyFormatting_invalid_record_error(self, testMapping, mocker):
        mocker.patch.multiple(DOABMapping,
            parseIdentifiers=mocker.MagicMock(return_value=[]),
            parseRights=mocker.MagicMock(return_value='testRights'),
            parseLinks=mocker.MagicMock(return_value='testLinks')
        )

        with pytest.raises(MappingError):
            testMapping.applyFormatting()

    def test_parseIdentifiers(self, testMapping):
        cleanIdentifiers = testMapping.parseIdentifiers()

        assert cleanIdentifiers == ['1|doab', '2|test', '00.00.00/0000|doi']

    def test_parseRights(self, testMapping):
        cleanRights = testMapping.parseRights()

        assert cleanRights == 'doab|license||statement|'

    def test_parseLinks(self, testMapping):
        cleanLinks = testMapping.parseLinks()

        assert cleanLinks == ['1|http://testURL|muse|testType|testFlags']
