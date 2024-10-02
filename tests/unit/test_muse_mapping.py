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
        mockRecord.languages = ['||lang1', '||lang2']
        mockRecord.dates = []

        return mockRecord

    @pytest.fixture
    def testMapping(self, testRecord, mocker):
        class TestMapping(MUSEMapping):
            def __init__(self):
                self.mapping = None
                self.record = testRecord
                self.source = {'008': mocker.MagicMock(data='testingdate2000pla')}
        
        return TestMapping()

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'identifiers', 'authors', 'title', 'alternative', 'has_version',
            'publisher', 'spatial', 'dates', 'languages', 'extent',
            'table_of_contents', 'abstract', 'subjects', 'contributors',
            'is_part_of', 'has_part'
        ]
        assert recordMapping['is_part_of'] == ('490', '{a}|{v}|volume')

    def test_applyFormatting(self, testMapping, mocker):

        mockCleanSubject = mocker.patch.object(MUSEMapping, 'clean_up_subject_head')
        mockCleanSubject.side_effect = [1, 2, 3]

        mockExtractLanguage = mocker.patch.object(MUSEMapping, 'extract_language')
        mockExtractLanguage.side_effect = ['lng1', 'lng2']

        testMapping.applyFormatting()

        assert testMapping.record.source == 'muse'
        assert testMapping.record.source_id == '1'
        assert testMapping.record.title == 'Main Title'
        assert testMapping.record.subjects == [1, 2, 3]
        assert testMapping.record.languages == ['lng1', 'lng2']
        assert testMapping.record.dates[0] == '2000|publication_date'

    def test_clean_up_subject_head(self, testMapping):
        cleanSubject = testMapping.clean_up_subject_head('first -- second. -- -- |||')

        assert cleanSubject == 'first -- second|||'

    def test_extract_language(self, testMapping):
        assert testMapping.extract_language('||100607s2011    mdu     o      00 0 eng d  z  ') == '||eng'

    def test_add_has_part_link(self, testMapping):
        testMapping.add_has_part_link('newURL', 'pdf+json', 'pdfFlags')

        assert testMapping.record.has_part[1] == '1|newURL|muse|pdf+json|pdfFlags'
