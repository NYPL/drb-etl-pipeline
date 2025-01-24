import pytest

from model import get_file_message
from processes.ingest.doab import DOABProcess
from tests.helper import TestHelpers

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
                self.s3_manager = mocker.MagicMock(s3Client=mocker.MagicMock())
                self.s3_bucket = 'test_aws_bucket'
                self.file_queue = 'test_file_queue'
                self.file_route = 'test_file_key'
                self.rabbitmq_manager = mocker.MagicMock()
                self.offset = 0
                self.limit = 10000
                self.ingestPeriod = None
                self.records = []
                self.dSpace_service = mocker.MagicMock()

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
            'generate_engine': mocker.patch.object(DOABProcess, 'generateEngine'),
            'create_session': mocker.patch.object(DOABProcess, 'createSession'),
            'save': mocker.patch.object(DOABProcess, 'saveRecords'),
            'commit': mocker.patch.object(DOABProcess, 'commitChanges'),
            'close': mocker.patch.object(DOABProcess, 'close_connection'),
            'manage_links': mocker.patch.object(DOABProcess, 'manage_links'),
        }

    def assert_common_expectations(self, mocks):
        mocks['generate_engine'].assert_called_once()
        mocks['create_session'].assert_called_once()
        mocks['save'].assert_called_once()
        mocks['commit'].assert_called_once()
        mocks['close'].assert_called_once()

    def test_runProcess_daily(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dSpace_service.get_records.return_value = record_mappings

        test_instance.process = 'daily'
        test_instance.runProcess()

        test_instance.dSpace_service.get_records.assert_called_once_with(offset=0, limit=10000)
        assert mocks['manage_links'].call_count == len(record_mappings)
        self.assert_common_expectations(mocks)

    def test_runProcess_complete(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dSpace_service.get_records.return_value = record_mappings

        test_instance.process = 'complete'
        test_instance.runProcess()

        test_instance.dSpace_service.get_records.assert_called_once_with(full_import=True, offset=0, limit=10000)
        assert mocks['manage_links'].call_count == len(record_mappings)
        self.assert_common_expectations(mocks)

    def test_runProcess_custom(self, test_instance: DOABProcess, record_mappings, mocks):
        test_instance.dSpace_service.get_records.return_value = record_mappings
        
        test_instance.process = 'custom'
        test_instance.runProcess()

        test_instance.dSpace_service.get_records.assert_called_once_with(start_timestamp=None, offset=0, limit=10000)
        assert mocks['manage_links'].call_count == len(record_mappings)
        self.assert_common_expectations(mocks)

    def test_runProcess_single(self, test_instance: DOABProcess, single_record_mapping, mocks):
        test_instance.dSpace_service.get_single_record.return_value = single_record_mapping
        
        test_instance.process = 'single'
        test_instance.singleRecord = 1
        test_instance.runProcess()

        test_instance.dSpace_service.get_single_record.assert_called_once_with(record_id=1, source_identifier='oai:directory.doabooks.org')
        assert mocks['manage_links'].call_count == 1
        self.assert_common_expectations(mocks)


    def test_manage_links_success(self, test_instance: DOABProcess, mocker):
        mock_record = mocker.MagicMock();

        mock_manager = mocker.MagicMock()
        mock_manager.manifests = [('pdfPath', 'pdfJSON')]
        mock_manager.ePubLinks = [(['epubPath', 'epubURI'])]
        
        mock_link_manager = mocker.patch('processes.ingest.doab.DOABLinkManager')
        mock_link_manager.return_value = mock_manager

        process_mocks = mocker.patch.multiple(DOABProcess, addDCDWToUpdateList=mocker.DEFAULT)

        test_instance.manage_links(mock_record)

        mock_manager.parseLinks.assert_called_once()
        test_instance.s3_manager.createManifestInS3.assert_called_once_with('pdfPath', 'pdfJSON', test_instance.s3_bucket)
        test_instance.rabbitmq_manager.sendMessageToQueue.assert_called_once_with(
            test_instance.file_queue, 
            test_instance.file_route, 
            get_file_message('epubURI', 'epubPath')
        )
        process_mocks['addDCDWToUpdateList'].assert_called_once()
