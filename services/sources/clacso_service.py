from datetime import datetime, timedelta, timezone
from io import BytesIO
from lxml import etree
from typing import Optional
import os
import requests

from mappings.clacso import CLACSOMapping
from constants.get_constants import get_constants
from logger import create_log
from .source_service import SourceService
from managers import RabbitMQManager, S3Manager

logger = create_log(__name__)

class CLACSOService(SourceService):
    CLACSO_BASE_URL = 'https://biblioteca-repositorio.clacso.edu.ar/oai/request?'
    ROOT_NAMESPACE = {None: 'http://www.openarchives.org/OAI/2.0/'}

    OAI_NAMESPACES = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'datacite': 'https://schema.datacite.org/meta/kernel-4.1/metadata.xsd',
        'oapen': 'http://purl.org/dc/elements/1.1/',
        'oaire': 'https://raw.githubusercontent.com/rcic/openaire4/master/schemas/4.0/oaire.xsd'
    }

    def __init__(self):

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']

        self.file_queue = os.environ['FILE_QUEUE']
        self.file_route = os.environ['FILE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.file_queue, self.file_route)

        self.constants = get_constants()

    def get_records(
        self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=0,
        limit: Optional[int]=100
    ) -> list[CLACSOMapping]:
        resumption_token = None
        records_processed = 0
        records = []
        
        while True:
            oai_file = self.download_oai_records(full_import, start_timestamp, resumption_token=resumption_token)

            resumption_token = self.get_resumption_token(oai_file)

            if records_processed < offset:
                records_processed += 100
                continue

            oai_dc_records = etree.parse(oai_file)

            for record in oai_dc_records.xpath('//oai_dc:dc', namespaces=self.OAI_NAMESPACES):
                if record is None: continue

                try:
                    parsed_record = CLACSOMapping(clacso_record=record, namespaces=self.OAI_NAMESPACES)
                    
                    if parsed_record.record:
                        records.append(parsed_record)
                        records_processed += 1

                    if limit is not None and records_processed >= limit:
                        return records
                except Exception:
                    logger.exception(f'Error parsing CLACSO record {record}')
            
            if not resumption_token:
                break
        
        return records
    
    def parse_clacso_record(self, oai_rec, namespaces):
        try:
            clacso_rec = CLACSOMapping(clacso_record=oai_rec, namespaces=namespaces)
            return clacso_rec
        except Exception as e:
            logger.exception(f'Error applying mapping to CLACSO Record')

    def download_oai_records(self, full_import, start_timestamp, resumption_token=None):
        headers = {
            # Pass a user-agent header to prevent 403 unauthorized responses from CLACSO
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        url_params = 'verb=ListRecords'
        if resumption_token:
            url_params = '{}&resumptionToken={}'.format(url_params, resumption_token)
        elif full_import is False:
            if not start_timestamp:
                start_timestamp = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)).strftime('%Y-%m-%d')
            url_params = '{}&metadataPrefix=oai_dc&from={}'.format(url_params, start_timestamp)
        else:
            url_params = '{}&metadataPrefix=oai_dc'.format(url_params)

        clacso_url = '{}{}'.format(self.CLACSO_BASE_URL, url_params)

        clacso_response = requests.get(clacso_url, stream=True, timeout=30, headers=headers)

        if clacso_response.status_code == 200:
            content = bytes()

            for chunk in clacso_response.iter_content(1024 * 100): content += chunk

            return BytesIO(content)

        raise Exception(f'Received {clacso_response.status_code} status code from {clacso_url}')   
    
    def get_resumption_token(self, oai_file):
        try:
            oai_xml = etree.parse(oai_file)
            return oai_xml.find('.//resumptionToken', namespaces=self.ROOT_NAMESPACE).text
        except AttributeError:
            return None
