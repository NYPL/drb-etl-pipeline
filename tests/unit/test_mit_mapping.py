import pytest

from mappings.mit import MITMapping


class TestMITMapping:
    @pytest.fixture
    def testMapping(self):
        class TestMIT(MITMapping):
            def __init__(self):
                self.mapping = None
        
        return TestMIT()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            title= 'testTitle',
            authors=['testAuthor|||true'],
            dates=['2023|publicationDate'],
            publisher='testPublisher',
            identifiers=['1', '2|isbn'],
            has_part=[('url', '1|testURL|mit|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')]
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'authors', 'dates', 'publisher',
            'identifiers', 'has_part'
        ]
        assert recordMapping['title'] == ('title', '{0}')
        assert recordMapping['authors'] == ('titleauthorname', '{0}|||true')
        assert recordMapping['dates'] == [('pubDate', '{0}|publication_date')]
        assert recordMapping['publisher'] == ('publisher', '{0}')
        assert recordMapping['identifiers'] == [('identifier', '{0}'), ('hcIsbn', '{0}|isbn'), ('pbIsbn', '{0}|isbn')]
        assert recordMapping['has_part'] == [('url', '1|{0}|mit|application/pdf|{{"catalog": false, "download": true, "reader": false, "embed": false}}')] 

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.spatial == 'Massachusetts'
        assert testMapping.record.source == 'mit'
        assert testMapping.record.source_id == 'mit_1'
        assert testMapping.record.identifiers == [
            '1', '2|isbn'
        ]
        

