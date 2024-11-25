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
            source='UofM Press',
            publisher_project_source=['University of Michigan']
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'rights', 'contributors', 'subjects',
            'source', 'publisher_project_source'
        ]
        assert recordMapping['title'] == ('Title', '{0}')

    def test_apply_formatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.apply_formatting()

        assert testMapping.record.has_part == []
        assert testMapping.record.source == 'UofM'
        assert testMapping.record.identifiers == ['testISBN|isbn', 'testOCLC|oclc']
        assert testMapping.record.source_id == 'UofM_testOCLC'
        assert testMapping.record.publisher == ['testPublisher||']
        assert testMapping.record.source == 'UofM'
        assert testMapping.record.publisher_project_source == 'University of Michigan'
        assert testMapping.record.subjects == ['testSubject||']
