import pytest

from mappings.core import Core


class TestCoreMapping:
    @pytest.fixture
    def testMapping(self, mocker):
        class TestCore(Core):
            def ___init__(self, source, statics):
                super(self, TestCore).__init__(source, statics)

            def createMapping(self):
                pass

        mockFormatter = mocker.patch('mappings.core.CustomFormatter')
        mockFormatter.return_value = 'mockFormatter'
        return TestCore('test', {'static': 'values'})

    def test_initializer(self, testMapping):
        assert testMapping.mapping == {}
        assert testMapping.source == 'test'
        assert testMapping.record == None
        assert testMapping.staticValues == {'static': 'values'}
        assert testMapping.formatter == 'mockFormatter'

    def test_initEmptyRecord(self, testMapping, mocker):
        mockUUID = mocker.patch('mappings.core.uuid4')
        mockUUID.return_value = 'testUUID'
        mockDate = mocker.patch('mappings.core.datetime')
        mockDate.utcnow.side_effect = ['testCreated', 'testModified']
        mockRecord = mocker.patch('mappings.core.Record')
        mockRecord.return_value = 'testRecord'

        testRecord = testMapping.initEmptyRecord()
        
        assert testRecord == 'testRecord'
        mockRecord.assert_called_once_with(
            uuid='testUUID', date_created='testCreated', date_modified='testModified',
            frbr_status='to_do', cluster_status=False
        )

    def test_applyMapping(self, testMapping, mocker):
        mockInitEmpty = mocker.patch.object(Core, 'initEmptyRecord')

        testMapping.applyMapping()

        mockInitEmpty.assert_called_once

    def test_applyFormatting(self, testMapping):
        assert testMapping.applyFormatting() is None

    def test_updateExisting(self, testMapping, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.__iter__.return_value = [
            ('uuid', 'uuid1'), ('title', 'Test Title')
        ]
        testMapping.record = mockRecord

        mockExisting = mocker.MagicMock()
        mockExisting.uuid = 'uuid2'
        mockExisting.frb_status = 'complete'

        testMapping.updateExisting(mockExisting)

        assert mockExisting.uuid == 'uuid2'
        assert mockExisting.title == 'Test Title'
        assert mockExisting.frbr_status == 'to_do'
        assert mockExisting.cluster_status == False