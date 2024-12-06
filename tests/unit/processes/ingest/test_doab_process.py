import datetime
from io import BytesIO
import pytest
import requests
from unittest import mock


from processes.ingest.doab import DOABProcess, DOABError
from mappings.base_mapping import MappingError
from model import get_file_message
from tests.helper import TestHelpers


class TestDOABProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testProcess(self, mocker):
        class TestDOAB(DOABProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.fileQueue = 'test_file_queue'
                self.fileRoute = 'test_file_key'
                self.constants = {}

                self.ingestOffset = 0
                self.ingestLimit = 10000
                self.records = []
                self.rabbitmq_manager = mocker.MagicMock()

        return TestDOAB()

    @pytest.fixture
    def testResumptionXML(self):
        xmlText = b'''<?xml version="1.0"?>
            <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
                <ListRecords>
                    <record/><record/>
                </ListRecords>
                <resumptionToken cursor="0">testToken</resumptionToken>
            </OAI-PMH>
        '''
        return BytesIO(xmlText)

    @pytest.fixture
    def mockOAIQuery(self, mocker):
        mockGet = mocker.patch.object(requests, 'get')
        mockResp = mocker.MagicMock()
        mockResp.status_code = 200
        mockResp.iter_content.return_value = [b'm', b'a', b'r', b'c']
        mockGet.return_value = mockResp

        return mockGet

    def test_runProcess_daily(self, testProcess, mocker):
        mockImport = mocker.patch.object(DOABProcess, 'importOAIRecords')
        mockSave = mocker.patch.object(DOABProcess, 'saveRecords')
        mockCommit = mocker.patch.object(DOABProcess, 'commitChanges')

        testProcess.process = 'daily'
        testProcess.runProcess()

        mockImport.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_complete(self, testProcess, mocker):
        mockImport = mocker.patch.object(DOABProcess, 'importOAIRecords')
        mockSave = mocker.patch.object(DOABProcess, 'saveRecords')
        mockCommit = mocker.patch.object(DOABProcess, 'commitChanges')

        testProcess.process = 'complete'
        testProcess.runProcess()

        mockImport.assert_called_once_with(fullOrPartial=True)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_custom(self, testProcess, mocker):
        mockImport = mocker.patch.object(DOABProcess, 'importOAIRecords')
        mockSave = mocker.patch.object(DOABProcess, 'saveRecords')
        mockCommit = mocker.patch.object(DOABProcess, 'commitChanges')

        testProcess.process = 'custom'
        testProcess.ingestPeriod = 'customTimestamp'
        testProcess.runProcess()

        mockImport.assert_called_once_with(startTimestamp='customTimestamp')
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_runProcess_single(self, testProcess, mocker):
        mockImport = mocker.patch.object(DOABProcess, 'importSingleOAIRecord')
        mockSave = mocker.patch.object(DOABProcess, 'saveRecords')
        mockCommit = mocker.patch.object(DOABProcess, 'commitChanges')

        testProcess.process = 'single'
        testProcess.singleRecord = 1
        testProcess.runProcess()

        mockImport.assert_called_once_with(1)
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_importSingleOAIRecord_success(self, testProcess, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 200
        mockResponse.content = b'testing'
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.return_value = mockResponse

        mockXML = mocker.MagicMock()
        mockXML.xpath.return_value = ['mockOAIRecord']
        mockEtree = mocker.patch('processes.ingest.doab.etree')
        mockEtree.parse.return_value = mockXML

        mockParseRecord = mocker.patch.object(DOABProcess, 'parseDOABRecord')

        testProcess.importSingleOAIRecord(1)

        mockGet.assert_called_once_with(
            'test_doab_urlverb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mockParseRecord.assert_called_once_with('mockOAIRecord')

    def test_importSingleOAIRecord_doab_error(self, testProcess, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 200
        mockResponse.content = b'testing'
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.return_value = mockResponse

        mockXML = mocker.MagicMock()
        mockXML.xpath.return_value = ['mockOAIRecord']
        mockEtree = mocker.patch('processes.ingest.doab.etree')
        mockEtree.parse.return_value = mockXML

        mockParseRecord = mocker.patch.object(DOABProcess, 'parseDOABRecord')
        mockParseRecord.side_effect = DOABError('test')

        testProcess.importSingleOAIRecord(1)

        mockGet.assert_called_once_with(
            'test_doab_urlverb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mockParseRecord.assert_called_once_with('mockOAIRecord')

    def test_importSingleOAIRecord_request_error(self, testProcess, mocker):
        mockResponse = mocker.MagicMock()
        mockResponse.status_code = 404
        mockResponse.content = b'testing'
        mockGet = mocker.patch.object(requests, 'get')
        mockGet.return_value = mockResponse

        mockEtree = mocker.patch('processes.ingest.doab.etree')
        mockParseRecord = mocker.patch.object(DOABProcess, 'parseDOABRecord')

        testProcess.importSingleOAIRecord(1)

        mockGet.assert_called_once_with(
            'test_doab_urlverb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mockEtree.parse.assert_not_called()
        mockParseRecord.assert_not_called()

    def test_importOAIRecords(self, testProcess, mocker):
        testProcess.ingestOffset = 100

        processMocks = mocker.patch.multiple(DOABProcess,
            downloadOAIRecords=mocker.DEFAULT,
            getResumptionToken=mocker.DEFAULT,
            parseDOABRecord=mocker.DEFAULT
        )
        processMocks['downloadOAIRecords'].side_effect = ['mock1', 'mock2', 'mock3']
        processMocks['getResumptionToken'].side_effect = ['res1', 'res2', None]

        mockElement = mocker.MagicMock(name='etreeElement')
        mockElement.xpath.side_effect = [['rec1', 'rec2', 'rec3'], ['rec4']]
        mockEtree = mocker.patch('processes.ingest.doab.etree')
        mockEtree.parse.return_value = mockElement

        processMocks['parseDOABRecord'].side_effect = [None, DOABError('test'), None, None]

        testProcess.importOAIRecords()

        processMocks['downloadOAIRecords'].assert_has_calls([
            mocker.call(False, None, resumptionToken=None),
            mocker.call(False, None, resumptionToken='res1'),
            mocker.call(False, None, resumptionToken='res2')
        ])
        mockEtree.parse.assert_has_calls([mocker.call('mock2'), mocker.call('mock3')])
        processMocks['parseDOABRecord'].assert_has_calls([
            mocker.call('rec1'), mocker.call('rec2'), mocker.call('rec3'), mocker.call('rec4')
        ])
    
    def test_getResumptionToken_success(self, testProcess, testResumptionXML):
        assert testProcess.getResumptionToken(testResumptionXML) == 'testToken'

    def test_getResupmtionToken_none(self, testProcess):
        endXML = BytesIO(b'<?xml version="1.0"?><OAI-PMH><ListRecords><record/></ListRecords></OAI-PMH>')

        assert testProcess.getResumptionToken(endXML) == None

    def test_downloadOAIRecords_complete(self, testProcess, mockOAIQuery):
        testRecords = testProcess.downloadOAIRecords(True, None)

        assert testRecords.read() == b'marc'
        mockOAIQuery.assert_called_once_with(
            'test_doab_urlverb=ListRecords&metadataPrefix=oai_dc',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_downloadOAIRecords_daily(self, testProcess, mockOAIQuery, mocker):
        mockDatetime = mocker.patch('processes.ingest.doab.datetime')
        mockDatetime.now.return_value.replace.return_value = datetime.datetime(1900, 1, 2)

        testRecords = testProcess.downloadOAIRecords(False, None)

        assert testRecords.read() == b'marc'
        mockOAIQuery.assert_called_once_with(
            'test_doab_urlverb=ListRecords&metadataPrefix=oai_dc&from=1900-01-01',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_downloadOAIRecords_custom(self, testProcess, mockOAIQuery):
        testRecords = testProcess.downloadOAIRecords(False, '2020-01-01')

        assert testRecords.read() == b'marc'
        mockOAIQuery.assert_called_once_with(
            'test_doab_urlverb=ListRecords&metadataPrefix=oai_dc&from=2020-01-01',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_downloadOAIRecords_error(self, testProcess, mockOAIQuery, mocker):
        errorMock = mocker.MagicMock()
        errorMock.status_code = 500
        mockOAIQuery.return_value = errorMock

        with pytest.raises(DOABError):
            testProcess.downloadOAIRecords(False, None)

    def test_downloadOAIRecords_resumption(self, testProcess, mockOAIQuery):
        testRecords = testProcess.downloadOAIRecords(False, None, 'testRes')

        assert testRecords.read() == b'marc'
        mockOAIQuery.assert_called_once_with(
            'test_doab_urlverb=ListRecords&resumptionToken=testRes',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_parseDOABRecord_success(self, testProcess, mocker):
        mockRecord = mocker.MagicMock()
        mockRecord.source_id = 'doab1'

        mockMapping = mocker.MagicMock()
        mockMapping.record = mockRecord
        mockMapper = mocker.patch('processes.ingest.doab.DOABMapping')
        mockMapper.return_value = mockMapping

        mockManager = mocker.MagicMock()
        mockManager.manifests = [('pdfPath', 'pdfJSON')]
        mockManager.ePubLinks = [(['epubPath', 'epubURI'])]
        
        mockLinkManager = mocker.patch('processes.ingest.doab.DOABLinkManager')
        mockLinkManager.return_value = mockManager

        processMocks = mocker.patch.multiple(DOABProcess, addDCDWToUpdateList=mocker.DEFAULT)

        testProcess.parseDOABRecord('testMARC')

        mockMapper.assert_called_once_with('testMARC', testProcess.OAI_NAMESPACES, {})
        mockMapping.applyMapping.assert_called_once()
        mockManager.parseLinks.assert_called_once()
        testProcess.s3_manager.createManifestInS3.assert_called_once_with('pdfPath', 'pdfJSON', testProcess.s3Bucket)
        testProcess.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            testProcess.fileQueue, 
            testProcess.fileRoute, 
            get_file_message('epubURI', 'epubPath')
        )
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mockMapping)

    def test_parseDOABRecord_error(self, testProcess, mocker):
        mockMapping = mocker.MagicMock()
        mockMapping.applyMapping.side_effect = MappingError('testError')
        mockMapper = mocker.patch('processes.ingest.doab.DOABMapping')
        mockMapper.return_value = mockMapping

        with pytest.raises(DOABError):
            testProcess.parseDOABRecord('testMARC')
