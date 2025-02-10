from datetime import datetime, timedelta, timezone
from typing import Optional
import requests
from io import BytesIO
from lxml import etree
from constants.get_constants import get_constants
from logger import create_log
from mappings.base_mapping import MappingError
from mappings.xml import XMLMapping
from .source_service import SourceService

logger = create_log(__name__)


class DSpaceService(SourceService):
    ROOT_NAMESPACE = {None: 'http://www.openarchives.org/OAI/2.0/'}
    OAI_NAMESPACES = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'datacite': 'https://schema.datacite.org/meta/kernel-4.1/metadata.xsd',
        'oapen': 'http://purl.org/dc/elements/1.1/',
        'oaire': 'https://raw.githubusercontent.com/rcic/openaire4/master/schemas/4.0/oaire.xsd'
    }

    def __init__(self, base_url, source_mapping: type[XMLMapping]):
        self.constants = get_constants()

        self.base_url = base_url
        self.source_mapping = source_mapping

    def get_records(self, full_import=False, start_timestamp=None, offset: Optional[int]=None, limit: Optional[int]=None):
        resumption_token = None

        records_processed = 0
        mapped_records = []
        while resumption_token is not None or records_processed <= offset:
            oai_file = self.download_records(
                full_import, start_timestamp, resumption_token=resumption_token)

            resumption_token = self.get_resumption_token(oai_file)

            if records_processed <= offset:
                records_processed += 100
                continue

            oaidc_records = etree.parse(oai_file)

            for record in oaidc_records.xpath('//oai_dc:dc', namespaces=self.OAI_NAMESPACES):
                if record is None:
                    continue

                try:
                    parsed_record = self.parse_record(record)
                    if parsed_record.record:
                        mapped_records.append(parsed_record)
                    else:
                        continue
                except Exception as e:
                    logger.error(f'Error parsing DSpace record {record}')

                records_processed += 1

                if limit is not None and records_processed >= limit:
                    return mapped_records

        return mapped_records

    def parse_record(self, record):
        try:
            parsed_record = self.source_mapping(record, self.OAI_NAMESPACES)
            return parsed_record
        except MappingError as e:
            raise Exception(e.message)

    def get_single_record(self, record_id, source_identifier):
        url = f'{self.base_url}verb=GetRecord&metadataPrefix=oai_dc&identifier={source_identifier}:{record_id}'

        response = requests.get(url, timeout=30)

        if response.status_code == 200:
            content = BytesIO(response.content)
            oaidc_XML = etree.parse(content)
            oaidc_record = oaidc_XML.xpath('//oai_dc:dc', namespaces=self.OAI_NAMESPACES)[0]

            try:
                parsed_record = self.parse_record(oaidc_record)
                return parsed_record
            except Exception as e:
                logger.error(f'Error parsing DSpace record {oaidc_record}')

    def get_resumption_token(self, oai_file):
        try:
            oai_XML = etree.parse(oai_file)
            return oai_XML.find('.//resumptionToken', namespaces=self.ROOT_NAMESPACE).text
        except AttributeError:
            return None

    def download_records(self, full_import, start_timestamp, resumption_token=None):
        headers = {
            # Pass a user-agent header to prevent 403 unauthorized responses from DSpace
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        url_params = 'verb=ListRecords'
        if resumption_token:
            url_params = f'{url_params}&resumptionToken={resumption_token}'
        elif full_import is False:
            if not start_timestamp:
                start_timestamp = (datetime.now(timezone.utc).replace(
                    tzinfo=None) - timedelta(hours=24)).strftime('%Y-%m-%d')
            url_params = f'{url_params}&metadataPrefix=oai_dc&from={start_timestamp}'
        else:
            url_params = f'{url_params}&metadataPrefix=oai_dc'

        url = f'{self.base_url}{url_params}'

        response = requests.get(url, stream=True, timeout=30, headers=headers)

        if response.status_code == 200:
            content = bytes()

            for chunk in response.iter_content(1024 * 100):
                content += chunk

            return BytesIO(content)

        raise Exception(
            f'Received {response.status_code} status code from {url}')
