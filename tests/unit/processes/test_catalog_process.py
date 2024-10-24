from lxml import etree
import pytest

from tests.helper import TestHelpers
from processes import CatalogProcess


class TestOCLCCatalogProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def testInstance(self, mocker):
        class TestCatalogProcess(CatalogProcess):
            def __init__(self, process, customFile, ingestPeriod):
                self.statics = {}
                self.oclcCatalogManager = mocker.MagicMock()
        
        return TestCatalogProcess('TestProcess', 'testFile', 'testDate')
    
    def test_runProcess(self, testInstance, mocker):
        mockReceive = mocker.patch.object(CatalogProcess, 'receiveAndProcessMessages')
        mockSave = mocker.patch.object(CatalogProcess, 'saveRecords')
        mockCommit = mocker.patch.object(CatalogProcess, 'commitChanges')

        testInstance.runProcess()

        mockReceive.assert_called_once
        mockSave.assert_called_once
        mockCommit.assert_called_once

    def test_receiveAndProcessMessages(self, testInstance, mocker):
        mockSleep = mocker.patch('processes.catalog.sleep')
        mockQueueGet = mocker.patch.object(CatalogProcess, 'getMessageFromQueue')
        mockProps = mocker.MagicMock()
        mockProps.delivery_tag = 'rabbitMQTag'
        mockQueueGet.side_effect = [
            (mockProps, {}, 'oclc_record'),
            (None, None, None),
            (None, None, None),
            (None, None, None),
            (None, None, None)
        ]
        mockProcess = mocker.patch.object(CatalogProcess, 'processCatalogQuery')
        mockAcknowledge = mocker.patch.object(CatalogProcess, 'acknowledgeMessageProcessed')

        testInstance.receiveAndProcessMessages()

        assert mockQueueGet.call_count == 5
        mockQueueGet.assert_called_with('test_oclc_queue')

        mockSleep.assert_has_calls([
            mocker.call(60), mocker.call(120), mocker.call(180)
        ])

        mockProcess.assert_called_once_with('oclc_record')
        mockAcknowledge.assert_called_once_with('rabbitMQTag')

    def test_processCatalogQuery_success(self, testInstance, mocker):
        testInstance.oclcCatalogManager.query_catalog.return_value = 'testXML'
        mockParser = mocker.patch.object(CatalogProcess, 'parseCatalogRecord')

        testInstance.processCatalogQuery('{"oclcNo": 1, "owiNo": 1}')

        testInstance.oclcCatalogManager.query_catalog.assert_called_once_with(1)
        mockParser.assert_called_once_with('testXML', 1, 1)

    def test_processCatalogQuery_no_record_found(self, testInstance, mocker):
        testInstance.oclcCatalogManager.query_catalog.return_value = None
        mockParser = mocker.patch.object(CatalogProcess, 'parseCatalogRecord')

        testInstance.processCatalogQuery('{"oclcNo": "badID"}')

        testInstance.oclcCatalogManager.query_catalog.assert_called_once_with('badID')
        mockParser.assert_not_called()

    def test_parseCatalogRecord_success(self, testInstance, mocker):
        mockXMLParser = mocker.patch.object(etree, 'fromstring')
        mockXMLParser.return_value = 'testMARC'

        mockCatalogRec = mocker.MagicMock(record=mocker.MagicMock(identifiers=[]))
        mockMapping = mocker.patch('processes.catalog.CatalogMapping')
        mockMapping.return_value = mockCatalogRec

        mockAdd = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        testInstance.parseCatalogRecord('rawXML', 1, 1)

        mockXMLParser.assert_called_once_with(b'rawXML')
        mockMapping.assert_called_once_with(
            'testMARC', {'oclc': 'http://www.loc.gov/MARC21/slim'}, {}
        )
        mockCatalogRec.applyMapping.assert_called_once()
        assert mockCatalogRec.record.identifiers[0] == '1|owi'
        mockAdd.assert_called_once_with(mockCatalogRec)

    def test_parseCatalogRecord_mapping_failure(self, testInstance, mocker):
        mockXMLParser = mocker.patch.object(etree, 'fromstring')
        mockXMLParser.return_value = 'testMARC'

        mockCatalogRec = mocker.MagicMock()
        mockCatalogRec.applyMapping.side_effect = Exception
        mockMapping = mocker.patch('processes.catalog.CatalogMapping')
        mockMapping.return_value = mockCatalogRec

        mockAdd = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        testInstance.parseCatalogRecord('rawXML', 1, 1)

        mockXMLParser.assert_called_once_with(b'rawXML')
        mockMapping.assert_called_once_with(
            'testMARC', {'oclc': 'http://www.loc.gov/MARC21/slim'}, {}
        )
        mockCatalogRec.applyMapping.assert_called_once()
        mockAdd.assert_not_called()

    def test_parseCatalogRecord_parsing_failure(self, testInstance, mocker):
        mockCatalogRec = mocker.MagicMock()
        mockMapping = mocker.patch('processes.catalog.CatalogMapping')
        mockMapping.return_value = mockCatalogRec

        mockAdd = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        testInstance.parseCatalogRecord('rawXML', 1, 1)

        mockMapping.assert_not_called()
        mockCatalogRec.applyMapping.assert_not_called()
        mockAdd.assert_not_called()
