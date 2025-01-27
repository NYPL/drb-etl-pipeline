from datetime import datetime, timezone, timedelta
from io import BytesIO
import pytest
import requests
from unittest import mock

from services import DSpaceService
from services.sources.dspace_service import DSpaceError
from mappings.base_mapping import MappingError
from processes.ingest.doab import DOABProcess

class TestDSpaceService:
    @pytest.fixture
    def test_instance(self, mocker):
        self.base_url = DOABProcess.DOAB_BASE_URL
        self.source_mapping = mocker.MagicMock()

        return DSpaceService(self.base_url, self.source_mapping)
    
    @pytest.fixture
    def test_resumption_XML(self):
        xmlText = b'''<?xml version="1.0"?>
            <OAI-PMH xmlns="http://www.openarchives.org/OAI/2.0/">
                <ListRecords>
                    <record/><record/>
                </ListRecords>
                <resumptionToken cursor="0">test_token</resumptionToken>
            </OAI-PMH>
        '''
        return BytesIO(xmlText)

    @pytest.fixture
    def mock_query(self, mocker):
        mock_get = mocker.patch.object(requests, 'get')
        mock_resp = mocker.MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'testing'
        mock_resp.iter_content.return_value = [b'm', b'a', b'r', b'c']
        mock_get.return_value = mock_resp

        return mock_get

    def test_get_records(self, test_instance: DSpaceService):
        records = test_instance.get_records(
            start_timestamp=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7),
            offset=0,
            limit=100
        )

        assert records is not None

    def test_get_single_record_success(self, test_instance: DSpaceService, mock_query, mocker):
        mock_XML = mocker.MagicMock()
        mock_XML.xpath.return_value = ['mock_record']
        mock_etree = mocker.patch('services.sources.dspace_service.etree')
        mock_etree.parse.return_value = mock_XML

        mock_parse_record = mocker.patch.object(DSpaceService, 'parse_record')

        test_instance.get_single_record(1, "oai:directory.doabooks.org")

        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mock_parse_record.assert_called_once_with('mock_record')

    def test_get_single_record_dspace_error(self, test_instance: DSpaceService, mock_query, mocker):
        mock_XML = mocker.MagicMock()
        mock_XML.xpath.return_value = ['mock_record']
        mock_etree = mocker.patch('services.sources.dspace_service.etree')
        mock_etree.parse.return_value = mock_XML

        mock_parse_record = mocker.patch.object(DSpaceService, 'parse_record')
        mock_parse_record.side_effect = DSpaceError('test')

        test_instance.get_single_record(1, "oai:directory.doabooks.org")

        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mock_parse_record.assert_called_once_with('mock_record')

    def test_get_single_record_request_error(self, test_instance: DSpaceService, mocker):
        mock_response = mocker.MagicMock()
        mock_response.status_code = 404
        mock_response.content = b'testing'
        mock_get = mocker.patch.object(requests, 'get')
        mock_get.return_value = mock_response

        mock_etree = mocker.patch('services.sources.dspace_service.etree')
        mock_parse_record = mocker.patch.object(DSpaceService, 'parse_record')

        test_instance.get_single_record(1, "oai:directory.doabooks.org")

        mock_get.assert_called_once_with(
            f'{test_instance.base_url}verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:1',
            timeout=30
        )
        mock_etree.parse.assert_not_called()
        mock_parse_record.assert_not_called()
    
    def test_get_resumption_token_success(self, test_instance: DSpaceService, test_resumption_XML):
        assert test_instance.get_resumption_token(test_resumption_XML) == 'test_token'

    def test_get_resumption_token_none(self, test_instance):
        end_XML = BytesIO(b'<?xml version="1.0"?><OAI-PMH><ListRecords><record/></ListRecords></OAI-PMH>')

        assert test_instance.get_resumption_token(end_XML) == None

    def test_download_records_complete(self, test_instance: DSpaceService, mock_query):
        test_records = test_instance.download_records(full_import=True, start_timestamp=None)

        assert test_records.read() == b'marc'
        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=ListRecords&metadataPrefix=oai_dc',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_download_records_daily(self, test_instance: DSpaceService, mock_query, mocker):
        mock_datetime = mocker.patch('services.sources.dspace_service.datetime')
        mock_datetime.now.return_value.replace.return_value = datetime(1900, 1, 2)

        test_records = test_instance.download_records(False, None)

        assert test_records.read() == b'marc'
        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=ListRecords&metadataPrefix=oai_dc&from=1900-01-01',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_download_records_custom(self, test_instance: DSpaceService, mock_query):
        test_records = test_instance.download_records(False, '2020-01-01')

        assert test_records.read() == b'marc'
        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=ListRecords&metadataPrefix=oai_dc&from=2020-01-01',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_download_records_error(self, test_instance: DSpaceService, mock_query, mocker):
        error_mock = mocker.MagicMock()
        error_mock.status_code = 500
        mock_query.return_value = error_mock

        with pytest.raises(DSpaceError):
            test_instance.download_records(False, None)

    def test_download_records_resumption(self, test_instance: DSpaceService, mock_query):
        test_records = test_instance.download_records(False, None, 'testRes')

        assert test_records.read() == b'marc'
        mock_query.assert_called_once_with(
            f'{test_instance.base_url}verb=ListRecords&resumptionToken=testRes',
            stream=True, 
            timeout=30,
            headers=mock.ANY
        )

    def test_parse_record_success(self, test_instance: DSpaceService, mocker):
        mock_record = mocker.MagicMock()
        mock_record.source_id = 'doab1'

        mock_mapping = mocker.MagicMock()
        mock_mapping.record = mock_record
        mock_mapper = test_instance.source_mapping
        mock_mapper.return_value = mock_mapping

        test_instance.parse_record('test_record')

        mock_mapper.assert_called_once_with('test_record', test_instance.OAI_NAMESPACES, test_instance.constants)
        mock_mapping.applyMapping.assert_called_once()

    def test_parse_record_error(self, test_instance: DSpaceService, mocker):
        mock_mapping = mocker.MagicMock()
        mock_mapping.applyMapping.side_effect = MappingError('test_error')
        mock_mapper = test_instance.source_mapping
        mock_mapper.return_value = mock_mapping

        with pytest.raises(DSpaceError):
            test_instance.parse_record('test_record')
