import pytest

from mappings.doab import DOABMapping


class TestDOABMapping:
    @pytest.fixture
    def testRecord(self, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.identifiers = ['1|doab', '2|test', '3|other']
        mockRecord.title = 'Main Title'
        mockRecord.subjects = ['subj1', 'subj2', 'subj3']
        mockRecord.has_part = ['1|testURL|muse|testType|testFlags']
        mockRecord.languages = ['||lang1', '||lang2']
        mockRecord.contributors = ['cont1||', 'cont2||']

        return mockRecord

    @pytest.fixture
    def testMapping(self, testRecord):
        class TestMapping(DOABMapping):
            def __init__(self):
                self.mapping = None
                self.record = testRecord
                self.staticValues = {'marc': {'contributorCodes': {'tst': 'Test'}}}
        
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
        mocker.patch.multiple(DOABMapping,
            cleanAndSplitLanguage=mocker.MagicMock(side_effect=[['lng1'], ['lng2']]),
            cleanUpSubjectHead=mocker.MagicMock(side_effect=['subj1', 'subj2', 'subj3']),
            parseContributorCode=mocker.MagicMock(side_effect=['cont1', 'cont2'])
        )

        testMapping.applyFormatting()

        assert testMapping.record.source == 'doab'
        assert testMapping.record.source_id == '1'
        assert testMapping.record.title == 'Main Title'
        assert testMapping.record.subjects == ['subj1', 'subj2', 'subj3']
        assert testMapping.record.languages == ['lng1', 'lng2']
        assert testMapping.record.contributors == ['cont1', 'cont2']
        assert list(testMapping.record.rights.split('|'))[0] == 'doab'

    def test_parseContributorCode(self, testMapping):
        assert testMapping.parseContributorCode('contrib|||tst') == 'contrib|||Test'

    def test_cleanUpSubjectHead(self, testMapping):
        cleanSubject = testMapping.cleanUpSubjectHead('first -- second. -- -- ||')

        assert cleanSubject == 'first -- second||'

    def test_cleanUpSubjectHead_authority(self, testMapping):
        cleanSubject = testMapping.cleanUpSubjectHead('first -- second. -- -- |0|')

        assert cleanSubject == 'first -- second|lcsh|'

    def test_cleanAndSplitLanguage(self, testMapping):
        assert testMapping.cleanAndSplitLanguage('English/deu||') == ['English||', '||deu']
