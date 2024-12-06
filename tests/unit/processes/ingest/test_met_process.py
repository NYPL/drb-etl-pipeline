from datetime import datetime
import pytest

from mappings.base_mapping import MappingError
from model import get_file_message
from processes.ingest.met import METProcess, METError
from tests.helper import TestHelpers


class TestMetProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestMET(METProcess):
            def __init__(self):
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock(db_manager=self.db_manager)
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.s3Bucket = 'test_aws_bucket'
                self.fileQueue = 'test_file_queue'
                self.fileRoute = 'test_file_key'
                self.records = []
                self.rabbitmq_manager = mocker.MagicMock()
        
        return TestMET()

    @pytest.fixture
    def testRecords(self, mocker):
        return [
            {'dmmodified': '2020-01-01', 'rights': 'public', 'pointer': 1},
            {'dmmodified': '2020-01-01', 'rights': 'copyrighted', 'pointer': 2},
            {'dmmodified': '2019-01-01', 'rights': 'public', 'pointer': 3},
            {'dmmodified': '2020-01-01', 'rights': 'public', 'pointer': 4}
        ]

    def test_runProcess(self, testProcess, mocker):
        runMocks = mocker.patch.multiple(
            METProcess,
            setStartTime=mocker.DEFAULT,
            importDCRecords=mocker.DEFAULT
        )

        testProcess.runProcess()
        
        runMocks['setStartTime'].assert_called_once()
        runMocks['importDCRecords'].assert_called_once()
        testProcess.record_buffer.flush.assert_called_once()

        testProcess.fullImport = True
        testProcess.startTimestamp = None

        testProcess.setStartTime()

        assert testProcess.startTimestamp is None

    def test_setStartTime_fullImport_false_daily(self, testProcess, mocker):
        testProcess.fullImport = False
        testProcess.startTimestamp = None
        testProcess.ingestPeriod = None

        mockDatetime = mocker.patch('processes.ingest.met.datetime')
        mockDatetime.now.return_value.replace.return_value = datetime(1900, 1, 2, 12, 0, 0)

        testProcess.setStartTime()

        assert testProcess.startTimestamp == datetime(1900, 1, 1, 12, 0, 0)

    def test_setStartTime_fullImport_false_custom(self, testProcess, mocker):
        testProcess.fullImport = False
        testProcess.startTimestamp = None
        testProcess.ingestPeriod = '2000-01-01T12:00:00'

        testProcess.setStartTime()

        assert testProcess.startTimestamp == datetime(2000, 1, 1, 12, 0, 0)

    def test_importDCRecords(self, testProcess, mocker):
        testProcess.ingestOffset = 0
        testProcess.ingestLimit = 1000

        mockQuery = mocker.patch.object(METProcess, 'queryMetAPI')
        mockProcess = mocker.patch.object(METProcess, 'processMetBatch')

        mockQuery.side_effect = [{'records': ['rec1', 'rec2', 'rec3']}, {'records': []}]       

        testProcess.importDCRecords()

        mockQuery.assert_has_calls([
            mocker.call('https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/p15324coll10/CISOSEARCHALL/title!dmmodified!dmcreated!rights/dmmodified/50/0/1/0/0/00/0/json'),
            mocker.call('https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmQuery/p15324coll10/CISOSEARCHALL/title!dmmodified!dmcreated!rights/dmmodified/50/50/1/0/0/00/0/json')
        ])

        mockProcess.assert_has_calls([mocker.call(['rec1', 'rec2', 'rec3']), mocker.call([])])

    def test_processMetBatch(self, testProcess, testRecords, mocker):
        testProcess.startTimestamp = datetime(2020, 1, 1, 0, 0, 0)
        mockProcess = mocker.patch.object(METProcess, 'processMetRecord')
        mockProcess.side_effect = [None, METError]

        testProcess.processMetBatch(testRecords)

        mockProcess.assect_has_calls([
            mocker.call(testRecords[0]), mocker.call(testRecords[3])
        ])

    def test_processMetRecord_success(self, testProcess, mocker):
        processMocks = mocker.patch.multiple(METProcess,
            queryMetAPI=mocker.DEFAULT,
            storePDFManifest=mocker.DEFAULT,
            addCoverAndStoreInS3=mocker.DEFAULT,
        )
        processMocks['queryMetAPI'].return_value = 'testDetail'

        mockMapping = mocker.MagicMock(record='testRecord')
        mockMapper = mocker.patch('processes.ingest.met.METMapping')
        mockMapper.return_value = mockMapping

        testProcess.processMetRecord({'pointer': 1, 'filetype': 'tst'})

        processMocks['queryMetAPI'].assert_called_once_with(
            'https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetItemInfo/p15324coll10/1/json'
        )

        mockMapper.assert_called_once_with('testDetail')
        mockMapping.applyMapping.assert_called_once()

        processMocks['storePDFManifest'].assert_called_once_with('testRecord')
        processMocks['addCoverAndStoreInS3'].assert_called_once_with('testRecord', 'tst')
        testProcess.record_buffer.add.assert_called_once_with(mockMapping)

    def test_processMetRecord_error(self, testProcess, mocker):
        mockQuery = mocker.patch.object(METProcess, 'queryMetAPI')
        mockQuery.return_value = 'testDetail'

        mockMapper = mocker.patch('processes.ingest.met.METMapping')
        mockMapper.side_effect = MappingError('testError')

        with pytest.raises(METError):
            testProcess.processMetRecord(mocker.MagicMock(pointer=1, filetype='tst'))

    def test_addCoverAndStoreInS3(self, testProcess, mocker):
        mockSetPath = mocker.patch.object(METProcess, 'setCoverPath')
        mockSetPath.return_value = 'testPath.jpg'

        testRecord = mocker.MagicMock(has_part=[], identifiers=['1|met'])
        testProcess.addCoverAndStoreInS3(testRecord, 'testType')

        assert testRecord.has_part[0] == '|https://test_aws_bucket.s3.amazonaws.com/covers/met/1.jpg|met|image/jpeg|{"cover": true}'
        mockSetPath.assert_called_once_with('testType', '1')
        testProcess.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            testProcess.fileQueue,
            testProcess.fileRoute,
            get_file_message('https://libmma.contentdm.oclc.org/digital/testPath.jpg', 'covers/met/1.jpg')
        )

    def test_setCoverPath_compound(self, testProcess, mocker):
        mockQuery = mocker.patch.object(METProcess, 'queryMetAPI')
        mockQuery.side_effect = [{'page': [{'pageptr': 1}]}, {'imageUri': 'testURI'}]

        assert testProcess.setCoverPath('cpd', 1) == 'testURI'
        mockQuery.assert_has_calls([
            mocker.call('https://libmma.contentdm.oclc.org/digital/bl/dmwebservices/index.php?q=dmGetCompoundObjectInfo/p15324coll10/1/json'),
            mocker.call('https://libmma.contentdm.oclc.org/digital/api/singleitem/collection/p15324coll10/id/1')
        ])

    def test_setCoverPath(self, testProcess):
        assert testProcess.setCoverPath('pdf', 1) == 'api/singleitem/image/pdf/p15324coll10/1/default.png'

    def test_storePDFManifest(self, testProcess, mocker):
        mockRecord = mocker.MagicMock(identifiers=['1|met'])
        mockRecord.has_part = [
            '1|testURI|met|text/html|{}',
            '1|testURI|met|application/pdf|{}',
            '2|testURIOther|met|application/pdf|{}',
        ]

        mockGenerateMan = mocker.patch.object(METProcess, 'generateManifest')
        mockGenerateMan.return_value = 'testJSON'

        testProcess.storePDFManifest(mockRecord)

        testManifestURI = 'https://test_aws_bucket.s3.amazonaws.com/manifests/met/1.json'
        assert mockRecord.has_part[0] == '1|{}|met|application/webpub+json|{{}}'.format(testManifestURI)

        mockGenerateMan.assert_called_once_with(mockRecord, 'testURI', testManifestURI)
        testProcess.s3_manager.createManifestInS3.assert_called_once_with('manifests/met/1.json', 'testJSON')

    def test_generateManifest(self, mocker):
        mockManifest = mocker.MagicMock(links=[])
        mockManifest.toJson.return_value = 'testJSON'
        mockManifestConstructor = mocker.patch('processes.ingest.met.WebpubManifest')
        mockManifestConstructor.return_value = mockManifest

        mockRecord = mocker.MagicMock(title='Test')
        testManifest = METProcess.generateManifest(mockRecord, 'sourceURI', 'manifestURI')

        assert testManifest == 'testJSON'
        assert mockManifest.links[0] == {'rel': 'self', 'href': 'manifestURI', 'type': 'application/webpub+json'}

        mockManifest.addMetadata.assert_called_once_with(mockRecord, conformsTo='test_profile_uri')
        mockManifest.addChapter.assert_called_once_with('sourceURI', 'Test')

    def test_queryMetAPI_success_non_head(self, mocker):
        mockResponse = mocker.MagicMock()
        mockRequests = mocker.patch('processes.ingest.met.requests')
        mockRequests.request.return_value = mockResponse

        mockResponse.json.return_value = 'testResponse'

        assert METProcess.queryMetAPI('testQuery') == 'testResponse'

        mockRequests.request.assert_called_once_with('GET', 'testQuery', timeout=30)

    def test_queryMetAPI_success_head(self, mocker):
        mockResponse = mocker.MagicMock(status_code=200)
        mockRequests = mocker.patch('processes.ingest.met.requests')
        mockRequests.request.return_value = mockResponse

        assert METProcess.queryMetAPI('testQuery', method='head') == 200

        mockRequests.request.assert_called_once_with('HEAD', 'testQuery', timeout=30)

    def test_queryMetAPI_error(self, mocker):
        mockResponse = mocker.MagicMock()
        mockRequests = mocker.patch('processes.ingest.met.requests')
        mockRequests.request.return_value = mockResponse

        mockResponse.raise_for_status.side_effect = Exception

        with pytest.raises(Exception):
            METProcess.queryMetAPI('testQuery')


