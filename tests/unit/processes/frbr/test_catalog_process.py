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
    def test_instance(self, mocker):
        class TestCatalogProcess(CatalogProcess):
            def __init__(self):
                self.constants = {}
                self.oclc_catalog_manager = mocker.MagicMock()
                self.records = []
                self.rabbitmq_manager = mocker.MagicMock()
        
        return TestCatalogProcess()
    
    def test_run_process(self, test_instance, mocker):
        mock_process_catalog_messages = mocker.patch.object(CatalogProcess, 'process_catalog_messages')
        mock_save = mocker.patch.object(CatalogProcess, 'saveRecords')
        mock_commit = mocker.patch.object(CatalogProcess, 'commitChanges')

        test_instance.runProcess()

        mock_process_catalog_messages.assert_called_once
        mock_save.assert_called_once
        mock_commit.assert_called_once

    def test_process_catalog_messages(self, test_instance, mocker):
        mock_sleep = mocker.patch('processes.frbr.catalog.sleep')
        mock_message_props = mocker.MagicMock()
        mock_message_props.delivery_tag = 'rabbitMQTag'
        test_instance.rabbitmq_manager.getMessageFromQueue.side_effect = [
            (mock_message_props, {}, 'oclc_record'),
            (None, None, None),
            (None, None, None),
            (None, None, None),
            (None, None, None)
        ]
        mock_process_catalog_message = mocker.patch.object(CatalogProcess, 'process_catalog_message')

        test_instance.process_catalog_messages()

        assert test_instance.rabbitmq_manager.getMessageFromQueue.call_count == 5
        test_instance.rabbitmq_manager.getMessageFromQueue.assert_called_with('test_oclc_queue')

        mock_sleep.assert_has_calls([
            mocker.call(60), mocker.call(120), mocker.call(180)
        ])

        mock_process_catalog_message.assert_called_once_with('oclc_record')
        test_instance.rabbitmq_manager.acknowledgeMessageProcessed.assert_called_once_with('rabbitMQTag')

    def test_process_catalog_message_success(self, test_instance, mocker):
        test_instance.oclc_catalog_manager.query_catalog.return_value = 'testXML'
        mock_parse_catalog_record = mocker.patch.object(CatalogProcess, 'parse_catalog_record')

        test_instance.process_catalog_message('{"oclcNo": 1, "owiNo": 1}')

        test_instance.oclc_catalog_manager.query_catalog.assert_called_once_with(1)
        mock_parse_catalog_record.assert_called_once_with('testXML', 1, 1)

    def test_process_catalog_message_no_record_found(self, test_instance, mocker):
        test_instance.oclc_catalog_manager.query_catalog.return_value = None
        mock_parse_catalog_message = mocker.patch.object(CatalogProcess, 'parse_catalog_record')

        test_instance.process_catalog_message('{"oclcNo": "badID"}')

        test_instance.oclc_catalog_manager.query_catalog.assert_called_once_with('badID')
        mock_parse_catalog_message.assert_not_called()

    def test_parse_catalog_record_success(self, test_instance, mocker):
        mock_etree_from_string = mocker.patch.object(etree, 'fromstring')
        mock_etree_from_string.return_value = 'testMARC'

        mock_catalog_record = mocker.MagicMock(record=mocker.MagicMock(identifiers=[]))
        mock_catalog_mapping = mocker.patch('processes.frbr.catalog.CatalogMapping')
        mock_catalog_mapping.return_value = mock_catalog_record

        mock_add_to_update_list = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        test_instance.parse_catalog_record('rawXML', 1, 1)

        mock_etree_from_string.assert_called_once_with(b'rawXML')
        mock_catalog_mapping.assert_called_once_with(
            'testMARC', {'oclc': 'http://www.loc.gov/MARC21/slim'}, {}
        )
        mock_catalog_record.applyMapping.assert_called_once()
        assert mock_catalog_record.record.identifiers[0] == '1|owi'
        mock_add_to_update_list.assert_called_once_with(mock_catalog_record)

    def test_parse_catalog_record_mapping_failure(self, test_instance, mocker):
        mock_etree_from_string = mocker.patch.object(etree, 'fromstring')
        mock_etree_from_string.return_value = 'testMARC'

        mock_catalog_record = mocker.MagicMock()
        mock_catalog_record.applyMapping.side_effect = Exception
        mock_catalog_mapping = mocker.patch('processes.frbr.catalog.CatalogMapping')
        mock_catalog_mapping.return_value = mock_catalog_record

        mock_add_to_update_list = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        test_instance.parse_catalog_record('rawXML', 1, 1)

        mock_etree_from_string.assert_called_once_with(b'rawXML')
        mock_catalog_mapping.assert_called_once_with(
            'testMARC', {'oclc': 'http://www.loc.gov/MARC21/slim'}, {}
        )
        mock_catalog_record.applyMapping.assert_called_once()
        mock_add_to_update_list.assert_not_called()

    def test_parse_catalog_record_parsing_failure(self, test_instance, mocker):
        mock_catalog_record = mocker.MagicMock()
        mock_catalog_mapping = mocker.patch('processes.frbr.catalog.CatalogMapping')
        mock_catalog_mapping.return_value = mock_catalog_record

        mock_add_to_update_list = mocker.patch.object(CatalogProcess, 'addDCDWToUpdateList')

        test_instance.parse_catalog_record('rawXML', 1, 1)

        mock_catalog_mapping.assert_not_called()
        mock_catalog_record.applyMapping.assert_not_called()
        mock_add_to_update_list.assert_not_called()
