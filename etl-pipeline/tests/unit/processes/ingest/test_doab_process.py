import dateutil
import dateutil.parser
import pytest
from unittest.mock import ANY

from model import get_file_message
from processes.ingest.doab import DOABProcess
from tests.helper import TestHelpers
from processes.utils import ProcessParams

class TestDOABProcess:
    @classmethod
    def setup_class(cls):
        TestHelpers.setEnvVars()

    @classmethod
    def teardown_class(cls):
        TestHelpers.clearEnvVars()

    @pytest.fixture
    def test_instance(self, mocker):
        class TestDOAB(DOABProcess):
            def __init__(self):
                self.params = ProcessParams()
                self.process = 'test_process'
                self.ingest_period = None
                self.single_record = 0
                self.db_manager = mocker.MagicMock()
                self.record_buffer = mocker.MagicMock()
                self.s3_manager = mocker.MagicMock(client=mocker.MagicMock())
                self.s3_bucket = 'test_aws_bucket'
                self.file_queue = 'test_file_queue'
                self.file_route = 'test_file_key'
                self.rabbitmq_manager = mocker.MagicMock()
                self.offset = 0
                self.limit = 10000
                self.records = []
                self.dspace_service = mocker.MagicMock()

        return TestDOAB()
    
    @pytest.fixture
    def single_record_mapping(self, mocker):
        return mocker.MagicMock()
    
    @pytest.fixture
    def record_mappings(self, mocker):
        return [mocker.MagicMock()]
    
    @pytest.fixture
    def mocks(self, mocker):
        return {
            '_process_record': mocker.patch.object(DOABProcess, '_process_record'),
        }

    def test_runProcess_daily(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dspace_service.get_records.return_value = record_mappings

        test_instance.params.process_type = 'daily'
        test_instance.runProcess()

        test_instance.dspace_service.get_records.assert_called_once_with(start_timestamp=ANY, offset=0, limit=None)
        assert mocks['_process_record'].call_count == len(record_mappings)

    def test_runProcess_complete(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dspace_service.get_records.return_value = record_mappings

        test_instance.params.process_type = 'complete'
        test_instance.runProcess()

        test_instance.dspace_service.get_records.assert_called_once_with(start_timestamp=None, offset=0, limit=None)
        assert mocks['_process_record'].call_count == len(record_mappings)

    def test_runProcess_custom(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dspace_service.get_records.return_value = record_mappings
        
        test_instance.params.ingest_period = '2022-01-01T12:00:00'
        test_instance.runProcess()

        test_instance.dspace_service.get_records.assert_called_once_with(start_timestamp=dateutil.parser.parse(test_instance.params.ingest_period), offset=0, limit=None)
        assert mocks['_process_record'].call_count == len(record_mappings)

    def test_runProcess_single(self, test_instance: DOABProcess, single_record_mapping, mocks):
        test_instance.dspace_service.get_single_record.return_value = single_record_mapping
        
        test_instance.params.record_id = 1
        test_instance.runProcess()

        test_instance.dspace_service.get_single_record.assert_called_once_with(record_id=1, source_identifier='oai:directory.doabooks.org')
        assert mocks['_process_record'].call_count == 1


    def test_manage_links_success(self, test_instance: DOABProcess, mocker):
        mock_record = mocker.MagicMock()

        mock_manager = mocker.MagicMock()
        mock_manager.manifests = [('pdfPath', 'pdfJSON')]
        mock_manager.epub_links = [(['epubPath', 'epubURI'])]
        
        mock_link_manager = mocker.patch('processes.ingest.doab.DOABLinkManager')
        mock_link_manager.return_value = mock_manager

        test_instance.manage_links(mock_record)

        mock_manager.parse_links.assert_called_once()
        test_instance.s3_manager.create_manifest_in_s3.assert_called_once_with('pdfPath', 'pdfJSON', test_instance.s3_bucket)
        test_instance.rabbitmq_manager.send_message_to_queue.assert_called_once_with(
            test_instance.file_queue, 
            test_instance.file_route, 
            get_file_message('epubURI', 'epubPath')
        )
