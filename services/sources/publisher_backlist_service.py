from datetime import datetime, timedelta, timezone
import json
import os
import requests
import urllib.parse
from typing import Optional
import traceback
from model import Record, Work, Edition
from urllib.parse import urlparse

from logger import create_log
from mappings.publisher_backlist import PublisherBacklistMapping
from managers import S3Manager, WebpubManifest
from .source_service import SourceService
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search, Q

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"
SOURCE_RECORD_ID_FIELD = 'DRB Record_ID'

class PublisherBacklistService(SourceService):
    def __init__(self):

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']
        self.prefix = 'manifests/publisher_backlist'
        self.db_manager = DBManager()
        self.db_manager.generateEngine()
        self.es_manager = ElasticsearchManager()
        self.es_manager.createElasticConnection()
        
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)

    def delete_records(
        self,
        limit: Optional[int]=None
    ):
        filter_by_formula = self.build_filter_by_formula_parameter(deleted=True)
        
        array_json_records = self.get_records_array(limit, filter_by_formula)

        self.db_manager.createSession()

        for json_record in array_json_records:
            records = json_record.get('records', [])
            
            for record in records:
                record_metadata = record.get('fields')
                
                if record_metadata:
                    record = self.db_manager.session.query(Record).filter(Record.source_id == record_metadata[SOURCE_RECORD_ID_FIELD]).first()

                    self.delete_record_digital_assets(record, record_metadata)
                    self.delete_record_data(record_metadata)
        
    def delete_record_digital_assets(self, record: Record):
        for part in record.has_part:
            _, link, *_ = part
            url = urlparse(link)
            bucket_name = url.hostname.split('.')[0]
            file_path = url.path.lstrip('/')

            self.s3_manager.s3Client.delete_object(Bucket=bucket_name, Key=file_path)


    def delete_record_data(self, record: Record):
        # TODO: delete record and corresponding data with record id
        record_uuid_str = str(record.uuid)
        edition =  self.db_manager.session.query(Edition).filter(Edition.dcdw_uuids.contains([record_uuid_str])).first()
        work = self.db_manager.session.query(Work).filter(Work.id == edition.work_id).first()
        if len(work.editions) == 1:
            work_uuid_str = str(work.uuid)
            es_work_resp = Search(index=os.environ['ELASTICSEARCH_INDEX']).query('match', uuid=work_uuid_str)
            self.db_manager.session.query(Work).filter(Work.id == edition.work_id).delete()
            es_work_resp.delete()
            self.db_manager.session.commit()
        else:
            self.delete_pub_backlist_edition_only(record.uuid_str, work)
            
    def delete_pub_backlist_edition_only(self, record_uuid_str, work):
        edition = self.db_manager.session.query(Edition) \
            .filter(Edition.work_id == work.id) \
            .filter(Edition.dcdw_uuids.contains([record_uuid_str])) \
            .first()
        self.db_manager.session.delete(edition)
        es_work_resp = Search(index=os.environ['ELASTICSEARCH_INDEX']).query('match', uuid=str(work.uuid))
        for work_hit in es_work_resp:
            for edition_hit in work_hit:
                edition_es_response = Search(index=os.environ['ELASTICSEARCH_INDEX']).query('nested', path='editions', query=Q('match', **{'editions.edition_id': edition_hit['edition_id']}))
                edition_es_response.delete()

    def get_records(
        self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[PublisherBacklistMapping]:
        array_json_records = self.get_records_json(full_import, start_timestamp, offset, limit)
        complete_records = []
        for json_dict in array_json_records:
            for records_value in json_dict['records']:
                try:
                    record_metadata_dict = records_value['fields']
                    pub_backlist_record = PublisherBacklistMapping(record_metadata_dict)
                    pub_backlist_record.applyMapping()
                    self.add_has_part_mapping(pub_backlist_record.record)
                    self.store_pdf_manifest(pub_backlist_record.record)
                    complete_records.append(pub_backlist_record)
                except Exception:
                    logger.exception(f'Failed to process Publisher Backlist record: {records_value}')
                    logger.error(traceback.format_exc())
        return complete_records
    
    def get_records_json(self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[dict]:
        if offset == None:
            limit = 100
            
        limit = offset
        
        filter_by_formula = self.build_filter_by_formula_parameter(deleted=False, full_import=full_import, start_timestamp=start_timestamp)
                
        array_json_records = self.get_records_array(limit, filter_by_formula)
        
        return array_json_records
        
    def build_filter_by_formula_parameter(self, deleted=None, full_import: bool=False, start_timestamp: datetime=None) -> str:
        if deleted:
            deleted_filter = f"IF(%7BDRB_Deleted%7D%20%3D%20TRUE(),%20TRUE(),%20FALSE())"
            filter_by_formula = f"&filterByFormula={deleted_filter}"
            return filter_by_formula
        
        is_not_deleted_filter = f"IF(%7BDRB_Deleted%7D%20!%3D%20TRUE(),%20TRUE(),%20FALSE())"

        if not start_timestamp:
            start_timestamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

        if_ready_to_ingest_is_true_filter = f"%20IF(%7BDRB_Ready%20to%20ingest%7D%20%3D%20TRUE(),%20TRUE(),%20FALSE())"

        if full_import:
            filter_by_formula = f'&filterByFormula={if_ready_to_ingest_is_true_filter}'
            return filter_by_formula
        else:
            start_date_time_str = start_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
            start_date_time_encoded = urllib.parse.quote(start_date_time_str)
            is_same_date_time_filter = f"IS_SAME(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22"
            is_after_date_time_filter = f"%20IS_AFTER(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22"

            filter_by_formula = f"&filterByFormula=AND(OR({is_same_date_time_filter}),{is_after_date_time_filter})),AND({if_ready_to_ingest_is_true_filter},{is_not_deleted_filter}))"

            return filter_by_formula
        
    def get_records_array(self,
        limit: Optional[int]=None, 
        filter_by_formula: str=None,
    ) -> list[dict]:
        url = f'{BASE_URL}&pageSize={limit}'
        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}

        if filter_by_formula:
            url += f'{filter_by_formula}'

        pub_backlist_records_response = requests.get(url, headers=headers)
        pub_backlist_records_response_json = pub_backlist_records_response.json()
        array_json = [pub_backlist_records_response_json]
        while 'offset' in pub_backlist_records_response_json:
            next_page_url = url + f"&offset={pub_backlist_records_response_json['offset']}"
            pub_backlist_records_response = requests.get(next_page_url, headers=headers)
            pub_backlist_records_response_json = pub_backlist_records_response.json()
            array_json.append(pub_backlist_records_response_json)

        return array_json
    
    def add_has_part_mapping(self, record: Record):
        # TODO: GOOGLE DRIVE API CALL TO GET PDF/EPUB FILES
        
        part_number = '1'
        file_link = 'https://link-to-pdf' # TODO: get link after implementing upload to S3
        file_type = 'application/pdf'
        link_flags = {
            'catalog': 'false',
            'download': 'true',
            'reader': 'true',
            'embed': 'false',
            'nypl_login': 'true' if 'in_copyright' in record.rights else 'false'
        }

        record.has_part.append('|'.join([part_number, file_link, record.source, file_type, json.dumps(link_flags)]))

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            item_no, url, source, media_type, flags = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]
                manifest_path = f'{self.prefix}/{source}/{record_id}.json'
                manifest_url = 'https://{}.s3.amazonaws.com/{}'.format(
                    self.s3_bucket, manifest_path
                )

                manifest_json = self.generate_manifest(record, url, manifest_url)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.s3_bucket)

                if 'in_copyright' in record.rights:
                    link_string = '|'.join([
                        item_no,
                        manifest_url,
                        source,
                        'application/webpub+json',
                        '{"catalog": false, "download": false, "reader": true, "embed": false, "fulfill_limited_access": false}'
                    ])

                    record.has_part.insert(0, link_string)
                    break

                if 'public_domain' in record.rights:
                    link_string = '|'.join([
                        item_no,
                        manifest_url,
                        source,
                        'application/webpub+json',
                        '{"catalog": false, "download": false, "reader": true, "embed": false}'
                    ])

                    record.has_part.insert(0, link_string)
                    break

    @staticmethod
    def generate_manifest(record, source_url, manifest_url):
        manifest = WebpubManifest(source_url, 'application/pdf')

        manifest.addMetadata(
            record,
            conformsTo=os.environ['WEBPUB_PDF_PROFILE']
        )
        
        manifest.addChapter(source_url, record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifest_url,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()
