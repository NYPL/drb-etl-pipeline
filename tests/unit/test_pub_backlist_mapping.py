import pytest

from mappings.publisher_backlist import PublisherBacklistMapping

class TestPublisherBacklistMapping:
    @pytest.fixture
    def test_mapping(self):
        class TestPublisherBacklistMapping(PublisherBacklistMapping):
            def __init__(self):
                self.mapping = None

        return TestPublisherBacklistMapping()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            title='testTitle',
            authors=['testAuthor|||true'],
            dates=['testDate|publication_date'],
            publisher=['testPublisher||'],
            identifiers=['testISBN|isbn', 'testOCLC|oclc'],
            rights='in copyright||||',
            contributor=['testContributor|||contributor'],
            subjects='testSubject',
            source=['UofMichigan Backlist'],
            source_id='testSourceID',
            publisher_project_source=['University of Michigan Press']
        )

    def test_createMapping(self, test_mapping):
        record_mapping = test_mapping.createMapping()

        assert list(record_mapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'rights', 'contributors', 'subjects',
            'source', 'source_id', 'publisher_project_source'
        ]
        assert record_mapping['title'] == ('Title', '{0}')

    def test_applyFormatting_standard(self, test_mapping, testRecordStandard):
        test_mapping.record = testRecordStandard

        test_mapping.applyFormatting()

        assert test_mapping.record.has_part == []
        assert test_mapping.record.source == 'UofMichigan'
        assert test_mapping.record.identifiers == ['testISBN|isbn', 'testOCLC|oclc']
        assert test_mapping.record.source_id == 'testSourceID'
        assert test_mapping.record.publisher == ['testPublisher||']
        assert test_mapping.record.publisher_project_source == 'University of Michigan Press'
        assert test_mapping.record.subjects == ['testSubject||']
