import pytest

from mappings.oclcClassify import ClassifyMapping


class TestClassifyMapping:
    @pytest.fixture
    def testMapping(self):
        class TestOCLCClassify(ClassifyMapping):
            def __init__(self):
                self.source = None
                self.mapping = None
                self.staticValues = None
                self.namespace = None
                self.sourceID = 1
                self.sourceIDType = 'classifyTest'

            def applyMapping(self):
                pass
        
        return TestOCLCClassify()

    @pytest.fixture
    def testRecord_standard(self, mocker):
        return mocker.MagicMock(
            identifiers=['1|owi', '2|test'],
            authors=['Test Author|||true', 'Test Editor [Editor]|||false', 'Test Other [Author, Editor]|||false'],
            contributors=[]
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'identifiers', 'authors', 'subjects'
        ]
        assert recordMapping['title'] == ('//oclc:work/@title', '{0}')

    def test_applyFormatting(self, testMapping, testRecord_standard):
        testMapping.record = testRecord_standard

        testMapping.applyFormatting()

        assert testMapping.record.source == 'oclcClassify'
        assert testMapping.record.source_id == '1|owi'
        assert testMapping.record.frbr_status == 'complete'
        assert testMapping.record.identifiers == ['1|owi', '2|test', '1|classifyTest']
        assert testMapping.record.authors == ['Test Author|||true', 'Test Other [Author, Editor]|||false']
        assert testMapping.record.contributors == ['Test Editor|||editor']

    def test_extendIdentifiers(self, testMapping, testRecord_standard):
        testMapping.record = testRecord_standard

        testMapping.extendIdentifiers(['3|test', '4|other']) 

        assert testMapping.record.identifiers == ['1|owi', '2|test', '3|test', '4|other']
