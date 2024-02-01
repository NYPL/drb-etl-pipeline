import pytest

from mappings.UofM import UofMMapping


class TestUofMMapping:
    @pytest.fixture
    def testMapping(self):
        class TestUofMMapping(UofMMapping):
            def __init__(self):
                self.mapping = None

        return TestUofMMapping()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            title='testTitle',
            authors=['testAuthor|||true'],
            dates=['testDate|publication_date'],
            publisher=['testPublisher||'],
            identifiers=['testISBN|isbn', 'testOCLC|oclc'],
            contributor=['testContributor|||contributor'],
            subjects='testSubject'
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'contributors', 'subjects'
        ]
        assert recordMapping['title'] == ('Title', '{0}')

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.has_part == []
        assert testMapping.record.source == 'UofM'
        assert testMapping.record.identifiers == ['testISBN|isbn', 'testOCLC|oclc']
        assert testMapping.record.source_id == 'UofM_testOCLC'
        assert testMapping.record.publisher == ['testPublisher||']
        assert testMapping.record.spatial == 'Michigan'
        assert testMapping.record.subjects == ['testSubject||']


