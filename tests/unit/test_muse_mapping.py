import pytest

from mappings.muse import MUSEMapping


class TestMUSEMapping:
    @pytest.fixture
    def testRecord(self, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.identifiers = ['1|muse', '2|test', '3|other']
        mockRecord.title = ['Main Title', 'Secondary Title']
        mockRecord.subjects = ['subj1', 'subj2', 'subj3']
        mockRecord.has_part = ['1|testURL|muse|testType|testFlags']

        return mockRecord

    @pytest.fixture
    def testMapping(self, testRecord):
        class TestMapping(MUSEMapping):
            def __init__(self):
                self.mapping = None
                self.record = testRecord
        
        return TestMapping()

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'identifiers', 'authors', 'title', 'alternative', 'has_version',
            'publisher', 'spatial', 'dates', 'extent', 'table_of_contents',
            'abstract', 'subjects', 'contributors', 'is_part_of', 'has_part'
        ]
        assert recordMapping['is_part_of'] == ('490', '{a}|{v}|volume')

    def test_applyFormatting(self, testMapping, mocker):

        mockCleanSubject = mocker.patch.object(MUSEMapping, 'cleanUpSubjectHead')
        mockCleanSubject.side_effect = [1, 2, 3]

        testMapping.applyFormatting()

        assert testMapping.record.source == 'muse'
        assert testMapping.record.source_id == '1'
        assert testMapping.record.title == 'Main Title'
        assert testMapping.record.subjects == [1, 2, 3]

    def test_cleanUpSubjectHead(self, testMapping):
        cleanSubject = testMapping.cleanUpSubjectHead('first -- second. -- -- |||')

        assert cleanSubject == 'first -- second|||'

    def test_addHasPartLink(self, testMapping):
        testMapping.addHasPartLink('newURL', 'pdf+json', 'pdfFlags')

        assert testMapping.record.has_part[1] == '2|newURL|muse|pdf+json|pdfFlags'
