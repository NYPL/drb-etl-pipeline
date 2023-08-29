import pytest

from mappings.loc import LOCMapping


class TestLOCMapping:
    @pytest.fixture
    def testMapping(self):
        class TestLOC(LOCMapping):
            def __init__(self):
                self.mapping = None

        return TestLOC()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            title='testTitle',
            alternative=['altTestTitle'],
            medium=['testMedium'],
            authors=['testAuthor|||true'],
            dates=['testDate'],
            publisher={
				"call_number": ["testCallNumber"],
				"created_published": ["testPubLocation : testPub"],
				"date": "testDate",
				"language": ["testLang"],
				"medium": ["testExtent"],
                "subjects": ['testSubject1', 'testSubject2'],
                'rights_advisory': ['testRights', 'testRights2']
            },
            identifiers=[['testLCCN|loc'], str({
				"call_number": ["testCallNumber"],
				"created_published": ["testPubLocation : testPub"],
                "date": "testDate",
				"language": ["testLang"],
		        "medium": ["testExtent"],
                "subjects": ['testSubject1', 'testSubject2'],
                'rights_advisory': ['testRights']
            })],
            contributor='testContributor|||contributor',
            extent={
				"call_number": ["testCallNumber",],
				"created_published": ["testPubLocation : testPub"],
				"date": "testDate",
				"language": ["testLang"],
				"medium": ["testExtent"],
                "subjects": ['testSubject1', 'testSubject2'],
                'rights_advisory': ['testRights']
            },
            is_part_of='testCollection|collection',
            abstract='testAbstract',
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'alternative', 'medium', 'authors', 'dates', 'publisher',
            'identifiers', 'contributors', 'extent', 'is_part_of', 'abstract'
        ]
        assert recordMapping['title'] == ('title', '{0}')

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.has_part == []
        assert testMapping.record.source == 'loc'
        assert testMapping.record.medium == 'testMedium'
        assert testMapping.record.identifiers == [
            'testLCCN|loc', 'testCallNumber|call_number'
        ]
        assert testMapping.record.source_id == 'testLCCN|loc'
        assert testMapping.record.publisher == ['testPub']
        assert testMapping.record.spatial == 'testPubLocation'
        assert testMapping.record.extent == 'testExtent'
        assert testMapping.record.subjects == ['testSubject1||', 'testSubject2||']
        assert testMapping.record.rights == 'loc|testRights|||'
        assert testMapping.record.languages == ['||testLang']

