import pytest

from mappings.core import MappingError
from processes.mit import MITProcess
from tests.helper import TestHelpers

class TestMITProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestMIT(MITProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3Client = mocker.MagicMock(s3Client='testS3Client')
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
        
        return TestMIT()

    def test_runProcess(self, testProcess, mocker):
        runMocks = mocker.patch.multiple(
            MITProcess,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT
        )

        testProcess.runProcess()

        runMocks['saveRecords'].assert_called_once()
        runMocks['commitChanges'].assert_called_once()


    def test_processMITRecord_success(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(MITProcess,
            storePDFManifest=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )

        mockMapping = mocker.MagicMock(record='testRecord')
        mockMapper = mocker.patch('processes.mit.MITMapping')
        mockMapper.return_value = mockMapping
        
        testProcess.processMITRecord(mockMapping)

        mockMapping.applyMapping.assert_called_once()

        processMocks['storePDFManifest'].assert_called_once_with('testRecord')
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_processmitRecord_error(self, mocker):

        mockMapper = mocker.patch('processes.mit.MITMapping')
        mockMapper.side_effect = MappingError('testError')

        assert pytest.raises(MappingError)

    def test_storePDFManifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1', '2|isbn]'])
        mockRecord.has_part = [
            '1|testURI|mit|application/pdf|{}'
        ]

        mockGenerateMan = mocker.patch.object(MITProcess, 'generateManifest')
        mockGenerateMan.return_value = 'testJSON'
        mockCreateMan = mocker.patch.object(MITProcess, 'createManifestInS3')

        testProcess.storePDFManifest(mockRecord)

        testManifestURI = 'https://test_aws_bucket.s3.amazonaws.com/manifests/mit/1.json'
        assert mockRecord.has_part[0] == '1|{}|mit|application/webpub+json|{{}}'.format(testManifestURI)

        mockGenerateMan.assert_called_once_with(mockRecord, 'testURI', testManifestURI)
        mockCreateMan.assert_called_once_with('manifests/mit/1.json', 'testJSON')

    def test_createManifestInS3(self, testProcess, mocker):
        mockPut = mocker.patch.object(MITProcess, 'putObjectInBucket')
        
        testProcess.createManifestInS3('testPath', '{"data": "testJSON"}')

        mockPut.assert_called_once_with(b'{"data": "testJSON"}', 'testPath', 'test_aws_bucket')

    def test_generateManifest(self, mocker):
        mockManifest = mocker.MagicMock(links=[])
        mockManifest.toJson.return_value = 'testJSON'
        mockManifestConstructor = mocker.patch('processes.mit.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        mockRecord = mocker.MagicMock(title='testTitle')
        testManifest = MITProcess.generateManifest(mockRecord, 'sourceURI', 'manifestURI')

        assert testManifest == 'testJSON'
        assert mockManifest.links[0] == {'rel': 'self', 'href': 'manifestURI', 'type': 'application/webpub+json'}

        mockManifest.addMetadata.assert_called_once_with(mockRecord, conformsTo='test_profile_uri')
        mockManifest.addChapter.assert_called_once_with('sourceURI', 'testTitle')