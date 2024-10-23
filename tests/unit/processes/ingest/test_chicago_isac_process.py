import pytest

from mappings.core import MappingError
from processes import ChicagoISACProcess
from tests.helper import TestHelpers

class TestChicagoISACProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestISAC(ChicagoISACProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3Client = mocker.MagicMock(s3Client='testS3Client')
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
        
        return TestISAC()

    def test_runProcess(self, testProcess, mocker):
        runMocks = mocker.patch.multiple(
            ChicagoISACProcess,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT
        )

        testProcess.run_process()

        runMocks['saveRecords'].assert_called_once()
        runMocks['commitChanges'].assert_called_once()


    def test_processChicagoISACRecord_success(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(ChicagoISACProcess,
            store_pdf_manifest=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )

        mockMapping = mocker.MagicMock(record='testRecord')
        mockMapper = mocker.patch('processes.ingest.chicago_isac.ChicagoISACMapping')
        mockMapper.return_value = mockMapping
        
        testProcess.process_chicago_isac_record(mockMapping)

        mockMapping.applyMapping.assert_called_once()

        processMocks['store_pdf_manifest'].assert_called_once_with('testRecord')
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_processChicagoISACRecord_error(self, mocker):

        mockMapper = mocker.patch('processes.ingest.chicago_isac.ChicagoISACMapping')
        mockMapper.side_effect = MappingError('testError')

        assert pytest.raises(MappingError)

    def test_store_pdf_manifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1|isac'])
        mockRecord.has_part = [
            ['1|testURI|isac|application/pdf|{}',
            '2|testURIOther|isac|application/pdf|{}'],
        ]

        mockGenerateMan = mocker.patch.object(ChicagoISACProcess, 'generate_manifest')
        mockGenerateMan.return_value = 'testJSON'
        mockCreateMan = mocker.patch.object(ChicagoISACProcess, 'createManifestInS3')

        testProcess.store_pdf_manifest(mockRecord)

        testManifestURI = 'https://test_aws_bucket.s3.amazonaws.com/manifests/isac/1.json'
        assert mockRecord.has_part[0] == '1|{}|isac|application/webpub+json|{{}}'.format(testManifestURI)

        mockGenerateMan.assert_called_once_with(mockRecord, 'testURI', testManifestURI)
        mockCreateMan.assert_called_once_with('manifests/isac/1.json', 'testJSON')

    def test_createManifestInS3(self, testProcess, mocker):
        mockPut = mocker.patch.object(ChicagoISACProcess, 'putObjectInBucket')
        
        testProcess.createManifestInS3('testPath', '{"data": "testJSON"}')

        mockPut.assert_called_once_with(b'{"data": "testJSON"}', 'testPath', 'test_aws_bucket')

    def test_generateManifest(self, mocker):
        mockManifest = mocker.MagicMock(links=[])
        mockManifest.toJson.return_value = 'testJSON'
        mockManifestConstructor = mocker.patch('processes.ingest.chicago_isac.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        mockRecord = mocker.MagicMock(title='testTitle')
        testManifest = ChicagoISACProcess.generate_manifest(mockRecord, 'sourceURI', 'manifestURI')

        assert testManifest == 'testJSON'
        assert mockManifest.links[0] == {'rel': 'self', 'href': 'manifestURI', 'type': 'application/webpub+json'}

        mockManifest.addMetadata.assert_called_once_with(mockRecord, conformsTo='test_profile_uri')
        mockManifest.addChapter.assert_called_once_with('sourceURI', 'testTitle')