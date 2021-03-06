import pytest

from mappings.hathitrust import HathiMapping


class TestHathingMapping:
    @pytest.fixture
    def testMapping(self, testStatics):
        class TestHathi(HathiMapping):
            def __init__(self):
                self.source = None
                self.mapping = None
                self.staticValues = testStatics

            def applyMapping(self):
                pass
        
        return TestHathi()

    @pytest.fixture
    def testRecord_standard(self, mocker):
        return mocker.MagicMock(
            identifiers=['1|hathi', '2|test'],
            dates=['Test Publisher [1900]|publication_date', '2000 [other]|copyright_date'],
            contributors=['contr|test'],
            rights='hathitrust|testLic|testReas||summary',
            spatial='tst  '
        )

    @pytest.fixture
    def testStatics(self):
        return {
            'hathitrust': {
                'sourceCodes': {'contr': 'Contributor'},
                'rightsValues': {'testLic': {'license': 'test', 'statement': 'Test License'}},
                'rightsReasons': {'testReas': 'Test Reason'}
            },
            'marc': {
                'countryCodes': {'tst': 'Test Country'}
            }
        }

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'identifiers', 'rights', 'is_part_of', 'title', 'dates', 'requires',
            'spatial', 'languages', 'contributors', 'authors'
        ]
        assert recordMapping['title'] == ('{}', 11)
        assert recordMapping['dates'] == [('{}|publication_date', 12), ('{}|copyright_date', 16)]

    def test_applyFormatting(self, testMapping, testRecord_standard):
        testMapping.record = testRecord_standard
        testMapping.source = ['recordID']

        testMapping.applyFormatting()

        assert testMapping.record.source == 'hathitrust'
        assert testMapping.record.source_id == '1|hathi'
        assert testMapping.record.dates == ['1900|publication_date', '2000 [other]|copyright_date']
        assert testMapping.record.publisher == 'Test Publisher||'
        assert testMapping.record.contributors == ['Contributor|test']
        assert testMapping.record.rights == 'test|Test Reason|Test License|summary'
        assert testMapping.record.has_part == [
            '1|https://babel.hathitrust.org/cgi/pt?id=recordID|hathitrust|text/html|{"reader": false, "download": false, "catalog": false}',
            '1|https://babel.hathitrust.org/cgi/imgsrv/download/pdf?id=recordID|hathitrust|application/pdf|{"reader": false, "download": true, "catalog": false}',
        ]
        assert testMapping.record.spatial == 'Test Country'

    def test_applyFormatting_no_pub_date(self, testMapping, testRecord_standard):
        testRecord_standard.dates = ['|publication_date']
        testMapping.record = testRecord_standard
        testMapping.source = ['recordID']

        testMapping.applyFormatting()

        assert testMapping.record.dates == []
        assert testMapping.record.publisher == '||'
        