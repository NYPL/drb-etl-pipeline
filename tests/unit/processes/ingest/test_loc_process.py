import pytest

from mappings.base_mapping import MappingError
from model import Record, get_file_message
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
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.session = mocker.MagicMock(session='testSession')
                self.records = mocker.MagicMock(record='testRecord')
                self.batchSize = mocker.MagicMock(batchSize='testBatchSize')
                self.process = 'complete'
                self.fileQueue = 'fileQueue'
                self.fileRoute = 'fileRoute'
                self.rabbitmq_manager = mocker.MagicMock()
        
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
        testProcess.s3_manager.store_pdf_manifest.assert_called_once_with(test_record, 'test_aws_bucket',
                                                                          flags='{"catalog": false, "reader": true, "embed": false, "download": false, "cover": false, "fulfill_limited_access": null}')
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

    def test_storeEpubsInS3(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1|loc'])
        mockRecord.has_part = [
            '1|testURI|loc|application/epub+zip|{"reader": false, "catalog": false, "download": true}',
        ]

        mockAddEPUBManifest = mocker.patch.object(LOCProcess, 'addEPUBManifest')

        testProcess.storeEpubsInS3(mockRecord)

        testProcess.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            testProcess.fileQueue,
            testProcess.fileRoute,
            get_file_message('testURI', 'epubs/loc/1.epub')
        )

        mockAddEPUBManifest.assert_has_calls([
            mocker.call(mockRecord, '1', 'loc', '{"reader": false, "catalog": false, "download": true}', 'application/epub+zip', 'epubs/loc/1.epub'),
        ])

    def test_addEPUBManifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(has_part=[])

        testProcess.addEPUBManifest(mockRecord, '1', 'loc', '{}', 'application/test', 'epubs/loc/1.epub')

        assert mockRecord.has_part[0] == '1|https://test_aws_bucket.s3.amazonaws.com/epubs/loc/1.epub|loc|application/test|{}'
