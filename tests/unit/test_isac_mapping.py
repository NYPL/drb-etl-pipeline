import pytest

from mappings.chicagoISAC import ChicagoISACMapping


class TestISACMapping:
    @pytest.fixture
    def testMapping(self):
        class TestISAC(ChicagoISACMapping):
            def __init__(self):
                self.source = {'isbn': '1112223334445'}
                self.mapping = None
        
        return TestISAC()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            title= 'testTitle',
            authors=['testAuthor|||true'],
            dates=['2023|publicationDate'],
            publisher='testPublisher',
            identifiers=['1, 2|isbn'],
            is_part_of = 'testSeries|series',
            spatial='testPubLocation|publisherLocation',
            extent='testExtent',
            has_part=[('url', '1|testURL|isac|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')],
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'is_part_of', 'spatial', 'extent', 'has_part'
        ]
        assert recordMapping['title'] == ('title', '{0}')
        assert recordMapping['authors'] == ('authors', '{0}|||true')
        assert recordMapping['dates'] == [('publicationDate', '{0}|publication_date')]
        assert recordMapping['publisher'] == ('publisher', '{0}')
        assert recordMapping['identifiers'] == [('isbn', '{0}|isbn')]
        assert recordMapping['is_part_of'] == ('series', '{0}|series')
        assert recordMapping['spatial'] == ('publisherLocation', '{0}')
        assert recordMapping['has_part'] == [('url', '1|{0}|isac|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.source == 'isac'
        assert testMapping.record.source_id == 'isac_1'
        assert testMapping.record.identifiers == [
            '1|isbn', '2|isbn'
        ]

