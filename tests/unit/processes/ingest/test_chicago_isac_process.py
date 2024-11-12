import pytest

from mappings.base_mapping import MappingError
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
    def test_process(self, mocker):
        class TestISAC(ChicagoISACProcess):
            def __init__(self):
                self.s3Bucket = 'test_aws_bucket'
                self.s3_client = mocker.MagicMock(s3_client='test_s3_client')
                self.session = mocker.MagicMock(session='test_session')
                self.records = mocker.MagicMock(record='test_record')
                self.batch_size = mocker.MagicMock(batch_size='test_batch_size')
        
        return TestISAC()

    def test_run_process(self, test_process, mocker):
        run_mocks = mocker.patch.multiple(
            ChicagoISACProcess,
            saveRecords=mocker.DEFAULT,
            commitChanges=mocker.DEFAULT
        )

        test_process.runProcess()

        run_mocks['saveRecords'].assert_called_once()
        run_mocks['commitChanges'].assert_called_once()


    def test_process_chicago_isac_record_success(self, test_process, mocker):
        processMocks = mocker.patch.multiple(ChicagoISACProcess,
            store_pdf_manifest=mocker.DEFAULT,
            addDCDWToUpdateList=mocker.DEFAULT
        )

        mock_mapping = mocker.MagicMock(record='test_record')
        mock_mapper = mocker.patch('processes.ingest.chicago_isac.ChicagoISACMapping')
        mock_mapper.return_value = mock_mapping
        
        test_process.process_chicago_isac_record(mock_mapping)

        mock_mapping.applyMapping.assert_called_once()

        processMocks['store_pdf_manifest'].assert_called_once_with('test_record')
        processMocks['addDCDWToUpdateList'].assert_called_once_with(mock_mapping)

    def test_process_chicago_isac_record_error(self, mocker):

        mock_mapper = mocker.patch('processes.ingest.chicago_isac.ChicagoISACMapping')
        mock_mapper.side_effect = MappingError('testError')

        assert pytest.raises(MappingError)

    def test_store_pdf_manifest(self, test_process, mocker):
        mock_record = mocker.MagicMock(identifiers=['1|isac'])
        mock_record.has_part = [
            ['1|test_url|isac|application/pdf|{}',
            '2|test_url_other|isac|application/pdf|{}'],
        ]

        mock_generate_man = mocker.patch.object(ChicagoISACProcess, 'generate_manifest')
        mock_generate_man.return_value = 'test_json'
        mock_create_man = mocker.patch.object(ChicagoISACProcess, 'createManifestInS3')

        test_process.store_pdf_manifest(mock_record)

        test_manifest_url = 'https://test_aws_bucket.s3.amazonaws.com/manifests/isac/1.json'
        assert mock_record.has_part[0] == '1|{}|isac|application/webpub+json|{{}}'.format(test_manifest_url)

        mock_generate_man.assert_called_once_with(mock_record, 'test_url', test_manifest_url)
        mock_create_man.assert_called_once_with('manifests/isac/1.json', 'test_json')

    def test_generate_manifest(self, mocker):
        mock_manifest = mocker.MagicMock(links=[])
        mock_manifest.toJson.return_value = 'test_json'
        mock_manifest_constructor = mocker.patch('processes.ingest.chicago_isac.WebpubManifest')
        mock_manifest_constructor.return_value = mock_manifest

        mock_record = mocker.MagicMock(title='test_title')
        test_manifest = ChicagoISACProcess.generate_manifest(mock_record, 'source_url', 'manifest_url')

        assert test_manifest == 'test_json'
        assert mock_manifest.links[0] == {'rel': 'self', 'href': 'manifest_url', 'type': 'application/webpub+json'}

        mock_manifest.addMetadata.assert_called_once_with(mock_record, conformsTo='test_profile_uri')
        mock_manifest.addChapter.assert_called_once_with('source_url', 'test_title')
