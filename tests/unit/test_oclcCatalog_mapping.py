import pytest

from mappings.oclcCatalog import CatalogMapping


class TestCatalogMapping:
    @pytest.fixture
    def testMapping(self):
        class TestOCLCCatalog(CatalogMapping):
            def __init__(self):
                self.source = None
                self.mapping = None
                self.staticValues = None
                self.namespace = None

            def applyMapping(self):
                pass
        
        return TestOCLCCatalog()

    @pytest.fixture
    def testRecord_standard(self, mocker):
        return mocker.MagicMock(
            identifiers=['1|oclc', '2|test'],
            languages=['||820305s1991####nyu###########001#0#eng##|']
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'alternative', 'authors', 'publisher', 'identifiers',
            'contributors', 'languages', 'dates', 'extent', 'is_part_of',
            'abstract', 'table_of_contents', 'subjects', 'has_part'
        ]
        assert recordMapping['title'] == ('//oclc:datafield[@tag=\'245\']/oclc:subfield[@code=\'a\' or @code=\'b\']/text()', '{0} {1}')

    def test_applyFormatting(self, testMapping, testRecord_standard):
        testMapping.record = testRecord_standard

        testMapping.applyFormatting()

        assert testMapping.record.source == 'oclcCatalog'
        assert testMapping.record.source_id == '1|oclc'
        assert testMapping.record.frbr_status == 'complete'
        assert testMapping.record.languages == ['||eng']
