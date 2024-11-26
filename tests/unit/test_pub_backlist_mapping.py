import pytest

from mappings.publisher_backlist import PublisherBacklistMapping

class TestPublisherBacklistMapping:
    @pytest.fixture
    def testMapping(self):
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

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'rights', 'contributors', 'subjects',
            'source', 'source_id', 'publisher_project_source'
        ]
        assert recordMapping['title'] == ('Title', '{0}')

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.has_part == []
        assert testMapping.record.source == 'UofMichigan'
        assert testMapping.record.identifiers == ['testISBN|isbn', 'testOCLC|oclc']
        assert testMapping.record.source_id == 'testSourceID'
        assert testMapping.record.publisher == ['testPublisher||']
        assert testMapping.record.publisher_project_source == 'University of Michigan Press'
        assert testMapping.record.subjects == ['testSubject||']
