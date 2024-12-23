from datetime import datetime, timedelta, timezone
import json
import os
import requests
import urllib.parse
from typing import Optional
import traceback
from model import Record, Work, Edition, Item
from urllib.parse import urlparse

from logger import create_log
from mappings.publisher_backlist import PublisherBacklistMapping
from managers import S3Manager, WebpubManifest
from .source_service import SourceService
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search, Q

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"


class PublisherBacklistService(SourceService):
    def __init__(self):
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.file_bucket = os.environ['FILE_BUCKET']

        self.db_manager = DBManager()
        self.db_manager.generateEngine()

        self.es_manager = ElasticsearchManager()
        self.es_manager.createElasticConnection()
        
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)

    def delete_records(self):        
        records = self.get_publisher_backlist_records(deleted=True)

        self.db_manager.createSession()

        for record in records:
            record_metadata = record.get('fields')

            if not record_metadata:
                continue
                
            record = self.db_manager.session.query(Record).filter(Record.source_id == record_metadata['DRB_Record ID']).first()

            if not record:
                continue

            try:
                self.delete_record_digital_assets(record, record_metadata)
                self.delete_record_data(record_metadata)
            except:
                logger.exception(f'Failed to delete record: {record.id}')

        self.db_manager.close_connection()
        
    def delete_record_digital_assets(self, record: Record):
        for part in record.has_part:
            _, link, *_ = part
            url = urlparse(link)
            bucket_name = url.hostname.split('.')[0]
            file_path = url.path.lstrip('/')

            self.s3_manager.s3Client.delete_object(Bucket=bucket_name, Key=file_path)

    def delete_record_data(self, record: Record):
        items = self.db_manager.query(Item).filter(Item.record_id == record.id).all()
        edition_ids = set([item.edition for item in items])

        for item in items:
            item.delete(synchronize_session=False)

        deleted_edition_ids = {}
        deleted_work_ids = set()
        work_ids = set()

        for edition_id in edition_ids:
            edition = self.db_manager.query(Edition).join(Item).filter(Edition.id == edition_id).first()

            if len(edition.items) == 0:
                edition.delete(synchronize_session=False)
                
                work_ids.add(edition.work_id)
                deleted_edition_ids[edition_id] = edition.work_id

        for work_id in work_ids:
            work = self.db_manager.query(Work).join(Edition).filter(Work.id == work_id).first()

            if len(work.editions) == 0:
                work.delete(synchronize_session=False)

                self.es_manager.client.delete(index=os.environ['ELASTICSEARCH_INDEX'], id=work.uuid)

                deleted_work_ids.add(work_id)
        
        for edition_id, work_id in deleted_edition_ids.items():
            if work_id not in deleted_work_ids:
                work_document = self.es_manager.client.get(index=os.environ['ELASTICSEARCH_INDEX'], id=work_id)
                editions = work_document['_source'].get('editions', [])
                
                updated_editions = [edition for edition in editions if edition.get('id') != edition_id]
                work_document['_source']['editions'] = updated_editions
                
                self.es_manager.client.index(index=os.environ['ELASTICSEARCH_INDEX'], id=work_id, body=work_document['_source'])

        self.db_manager.session.commit()

    def get_records(
        self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[PublisherBacklistMapping]:
        records = self.get_publisher_backlist_records(deleted=False, full_import=full_import, start_timestamp=start_timestamp, offset=offset, limit=limit)
        mapped_records = []
        
        for record in records:
            try:
                record_metadata = record.get('fields')
                
                publisher_backlist_record = PublisherBacklistMapping(record_metadata)
                publisher_backlist_record.applyMapping()
                
                self.add_has_part_mapping(publisher_backlist_record.record)
                self.store_pdf_manifest(publisher_backlist_record.record)
                
                mapped_records.append(publisher_backlist_record)
            except Exception:
                logger.exception(f'Failed to process Publisher Backlist record: {record_metadata}')
                logger.error(traceback.format_exc())
        
        return mapped_records
        
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
        
    def get_publisher_backlist_records(self,
        deleted: bool=False,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[dict]:
        filter_by_formula = self.build_filter_by_formula_parameter(deleted=deleted, full_import=full_import, start_timestamp=start_timestamp)
        url = f'{BASE_URL}&pageSize={limit}{filter_by_formula}'
        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}
        publisher_backlist_records = []

        records_response = requests.get(url, headers=headers)
        records_response_json = records_response.json()
        
        publisher_backlist_records.extend(records_response_json.get('records', []))
        
        while 'offset' in records_response_json:
            next_page_url = url + f"&offset={records_response_json['offset']}"
            
            records_response = requests.get(next_page_url, headers=headers)
            records_response_json = records_response.json()
            
            publisher_backlist_records.extend(records_response_json.get('records', []))

        return publisher_backlist_records
    
    def add_has_part_mapping(self, record: Record):
        # TODO: GOOGLE DRIVE API CALL TO GET PDF/EPUB FILES
        
        item_no = '1'
        url = 'https://link-to-pdf' # TODO: get link after implementing upload to S3
        media_tpye = 'application/pdf'
        flags = {
            'catalog': 'false',
            'download': 'true',
            'reader': 'true',
            'embed': 'false',
            'nypl_login': 'true' if 'in_copyright' in record.rights else 'false'
        }

        record.has_part.append('|'.join([item_no, url, record.source, media_tpye, json.dumps(flags)]))

    def store_pdf_manifest(self, record: Record):
        for link in record.has_part:
            item_no, url, source, media_type, flags = link.split('|')

            if media_type == 'application/pdf':
                manifest_path = f'manifests/publisher_backlist/{source}/{record.id}.json'
                manifest_url = f'https://{self.file_bucket}.s3.amazonaws.com/{manifest_path}'

                manifest_json = self.generate_manifest(record, url, manifest_url)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.file_bucket)

                record.has_part.insert(0, '|'.join([item_no, manifest_url, source, 'application/webpub+json', flags]))
                
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
