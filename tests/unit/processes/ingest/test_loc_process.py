import pytest

from mappings.core import MappingError
from model import Record
from processes import LOCProcess
from tests.helper import TestHelpers

class TestLOCProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestLOC(LOCProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3Client = mocker.MagicMock(s3Client='testS3Client')
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
                self.process = 'complete'
        
        return TestLOC()

    def test_runProcess(self, testProcess, mocker):
        runMocks = mocker.patch.multiple(
            LOCProcess,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT,
            importLOCRecords=mocker.DEFAULT
        )

        testProcess.runProcess()

        runMocks['importLOCRecords'].assert_called_once_with()
        runMocks['saveRecords'].assert_called_once()
        runMocks['commitChanges'].assert_called_once()


    def test_processLOCRecord_success(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(LOCProcess,
            addHasPartMapping=mocker.DEFAULT,
            storePDFManifest=mocker.DEFAULT,
            storeEpubsInS3=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )

        test_record = Record(authors=[])

        mockMapping = mocker.MagicMock()
        mockMapping.record = test_record
        mockMapper = mocker.patch('processes.ingest.loc.LOCMapping')
        mockMapper.return_value = mockMapping
        
        testProcess.processLOCRecord(mockMapping)

        mockMapping.applyMapping.assert_called_once()

        processMocks['addHasPartMapping'].assert_called_once_with(mockMapping, test_record)
        processMocks['storePDFManifest'].assert_called_once_with(test_record)
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_processlocRecord_error(self, mocker):

        mockMapper = mocker.patch('processes.ingest.loc.LOCMapping')
        mockMapper.side_effect = MappingError('testError')

        assert pytest.raises(MappingError)

    def test_addHasPartMapping(self, testProcess, mocker):
       testResultsRecord = {'resources': [{'pdf': 'testPDF', 'epub_file': 'testEPUB'}]}
       mockRecord = mocker.MagicMock(has_part=[])
       
       testProcess.addHasPartMapping(testResultsRecord, mockRecord)
       
       assert mockRecord.has_part[0] == '1|testPDF|loc|application/pdf|{"catalog": false, "download": true, "reader": false, "embed": false}'

    def test_storePDFManifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1|loc'])
        mockRecord.has_part = [
            '1|testURI|loc|application/pdf|{}',
            '1|testURIOther|loc|application/epub+zip|{}',
        ]

        mockGenerateMan = mocker.patch.object(LOCProcess, 'generateManifest')
        mockGenerateMan.return_value = 'testJSON'
        mockCreateMan = mocker.patch.object(LOCProcess, 'createManifestInS3')

        testProcess.storePDFManifest(mockRecord)

        testManifestURI = 'https://test_aws_bucket.s3.amazonaws.com/manifests/loc/1.json'
        assert mockRecord.has_part[0] == '1|{}|loc|application/webpub+json|{{"catalog": false, "download": false, "reader": true, "embed": false}}'.format(testManifestURI)

        mockGenerateMan.assert_called_once_with(mockRecord, 'testURI', testManifestURI)
        mockCreateMan.assert_called_once_with('manifests/loc/1.json', 'testJSON')

    def test_storeEpubsInS3(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1|loc'])
        mockRecord.has_part = [
            '1|testURI|loc|application/epub+zip|{"reader": false, "catalog": false, "download": true}',
        ]

        mockSendToQueue = mocker.patch.object(LOCProcess, 'sendFileToProcessingQueue')
        mockAddEPUBManifest = mocker.patch.object(LOCProcess, 'addEPUBManifest')

        testProcess.storeEpubsInS3(mockRecord)

        mockSendToQueue.assert_has_calls([
            mocker.call('testURI', 'epubs/loc/1.epub'),
        ])

        mockAddEPUBManifest.assert_has_calls([
            mocker.call(mockRecord, '1', 'loc', '{"reader": false, "catalog": false, "download": true}', 'application/epub+zip', 'epubs/loc/1.epub'),
        ])

    def test_createManifestInS3(self, testProcess, mocker):
        mockPut = mocker.patch.object(LOCProcess, 'putObjectInBucket')
        
        testProcess.createManifestInS3('testPath', '{"data": "testJSON"}')

        mockPut.assert_called_once_with(b'{"data": "testJSON"}', 'testPath', 'test_aws_bucket')

    def test_addEPUBManifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(has_part=[])

        testProcess.addEPUBManifest(mockRecord, '1', 'loc', '{}', 'application/test', 'epubs/loc/1.epub')

        assert mockRecord.has_part[0] == '1|https://test_aws_bucket.s3.amazonaws.com/epubs/loc/1.epub|loc|application/test|{}'

    def test_generateManifest(self, mocker):
        mockManifest = mocker.MagicMock(links=[])
        mockManifest.toJson.return_value = 'testJSON'
        mockManifestConstructor = mocker.patch('processes.ingest.loc.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        mockRecord = mocker.MagicMock(title='testTitle')
        testManifest = LOCProcess.generateManifest(mockRecord, 'sourceURI', 'manifestURI')

        assert testManifest == 'testJSON'
        assert mockManifest.links[0] == {'rel': 'self', 'href': 'manifestURI', 'type': 'application/webpub+json'}

        mockManifest.addMetadata.assert_called_once_with(mockRecord, conformsTo='test_profile_uri')
        mockManifest.addChapter.assert_called_once_with('sourceURI', 'testTitle')