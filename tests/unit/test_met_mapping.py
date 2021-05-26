import pytest

from mappings.met import METMapping


class TestMETMapping:
    @pytest.fixture
    def testMapping(self):
        class TestMET(METMapping):
            def __init__(self):
                self.source = {'dmrecord': 1}
                self.mapping = None
        
        return TestMET()

    @pytest.fixture
    def testRecordStandard(self, mocker):
        return mocker.MagicMock(
            identifiers=['1|met', '2|test', '3|oclc'],
            subjects=['first ; second||'],
            has_part=[],
            abstract = ['', 'test abstract']
        )

    def test_createMapping(self, testMapping):
        recordMapping = testMapping.createMapping()

        assert list(recordMapping.keys()) == [
            'title', 'alternate', 'authors', 'languages', 'dates', 'publisher',
            'identifiers', 'contributors', 'extent', 'is_part_of', 'abstract',
            'subjects', 'rights', 'has_part'
        ]
        assert recordMapping['title'] == ('title', '{0}')

    def test_applyFormatting_standard(self, testMapping, testRecordStandard):
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.source == 'met'
        assert testMapping.record.source_id == '1|met'
        assert testMapping.record.subjects == ['first||', 'second||']
        assert testMapping.record.abstract == 'test abstract'
        assert testMapping.record.has_part == [
            '1|https://libmma.contentdm.oclc.org/digital/api/collection/p15324coll10/id/1/download|met|application/pdf|{}',
        ]

    def test_applyFormatting_missing_fields(self, testMapping, testRecordStandard):
        testRecordStandard.abstract = ['', '']
        testRecordStandard.subjects = []
        testMapping.record = testRecordStandard

        testMapping.applyFormatting()

        assert testMapping.record.subjects is None
        assert testMapping.record.abstract is None

