from datetime import datetime, timedelta, timezone
import json
import os
import requests
import urllib.parse
from enum import Enum
from typing import Optional
from model import Record, Work, Edition, Item
from sqlalchemy.orm import joinedload

from logger import create_log
from mappings.publisher_backlist import PublisherBacklistMapping
from managers import S3Manager, WebpubManifest
from services.ssm_service import SSMService
from services.google_drive_service import GoogleDriveService
from .source_service import SourceService
from managers import DBManager, ElasticsearchManager

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"

SOURCE_FIELD = "Project Name (from Project)"

class LimitedAccessPermissions(Enum):
    FULL_ACCESS = 'Full access'
    PARTIAL_ACCESS = 'Partial access/read only/no download/no login'
    LIMITED_DOWNLOADABLE = 'Limited access/login for read & download'
    LIMITED_WITHOUT_DOWNLOAD = 'Limited access/login for read/no download'

class PublisherBacklistService(SourceService):
    def __init__(self):
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.title_prefix = 'titles/publisher_backlist'
        self.file_bucket = os.environ['FILE_BUCKET']
        self.limited_file_bucket = f'drb-files-limited-{os.environ.get("ENVIRONMENT", "qa")}'

        self.drive_service = GoogleDriveService()

        self.db_manager = DBManager()
        self.db_manager.generateEngine()

        self.es_manager = ElasticsearchManager()
        self.es_manager.createElasticConnection()

        self.ssm_service = SSMService()
        self.airtable_auth_token = self.ssm_service.get_parameter('airtable/pub-backlist/api-key')

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
                self.delete_record_digital_assets(record)
                self.delete_record_data(record)
            except:
                logger.exception(f'Failed to delete record: {record.id}')

        self.db_manager.close_connection()
        
    def delete_record_digital_assets(self, record: Record):
        for part in record.has_part:
            _, link, *_ = part.split('|')
            url = urllib.parse.urlparse(link)
            bucket_name = url.hostname.split('.')[0]
            file_path = url.path.lstrip('/')

            self.s3_manager.s3Client.delete_object(Bucket=bucket_name, Key=file_path)

    def delete_record_data(self, record: Record):
        items = self.db_manager.session.query(Item).filter(Item.record_id == record.id).all()
        edition_ids = set([item.edition_id for item in items])

        self.db_manager.session.delete(record)

        for item in items:
            self.db_manager.session.delete(item)

        self.db_manager.session.commit()

        deleted_edition_ids = {}
        deleted_work_ids = set()
        work_ids = set()
        work_ids_to_uuids = {}

        for edition_id in edition_ids:
            edition = (
                self.db_manager.session.query(Edition)
                    .options(
                        joinedload(Edition.items)
                    )
                    .filter(Edition.id == edition_id)
                    .first()
            )

            if edition and not edition.items:
                self.db_manager.session.delete(edition)
                
                work_ids.add(edition.work_id)
                deleted_edition_ids[edition_id] = edition.work_id

        self.db_manager.session.commit()

        for work_id in work_ids:
            work = (
                self.db_manager.session.query(Work)
                    .options(
                        joinedload(Work.editions)
                    )
                    .filter(Work.id == work_id)
                    .first()
            )
            work_ids_to_uuids[work.id] = work.uuid

            if work and not work.editions:
                self.db_manager.session.delete(work)

                self.es_manager.client.delete(index=os.environ['ELASTICSEARCH_INDEX'], id=work.uuid)

                deleted_work_ids.add(work_id)

        self.db_manager.session.commit()
        
        for edition_id, work_id in deleted_edition_ids.items():
            if work_id not in deleted_work_ids:
                work_uuid = work_ids_to_uuids[work_id]
                work_document = self.es_manager.client.get(index=os.environ['ELASTICSEARCH_INDEX'], id=work_uuid)
                editions = work_document['_source'].get('editions', [])
                
                updated_editions = [edition for edition in editions if edition.get('id') != edition_id]
                work_document['_source']['editions'] = updated_editions
                
                self.es_manager.client.index(index=os.environ['ELASTICSEARCH_INDEX'], id=work_uuid, body=work_document['_source'])

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
                try:
                    file_id = f'{self.drive_service.id_from_url(record_metadata.get("DRB_File Location"))}'
                except Exception:
                    logger.error(f'Could not extract a Drive identifier from {record_metadata.get("DRB_Record ID")}')
                    continue
                file_name = self.drive_service.get_file_metadata(file_id).get('name')
                file = self.drive_service.get_drive_file(file_id)
                
                if not file:
                    logger.error(f'Failed to retrieve file for {record_metadata.get("DRB_Record ID")} from Google Drive')
                    continue

                record_permissions = self.parse_permissions(record_metadata.get('Access type in DRB (from Access types)')[0])
                if not record_permissions['is_login_limited']:
                    bucket = self.file_bucket
                else:
                    bucket = self.limited_file_bucket
                s3_path = f'{self.title_prefix}/{record_metadata[SOURCE_FIELD][0]}/{file_name}'
                s3_response = self.s3_manager.putObjectInBucket(file.getvalue(), s3_path, bucket)
                
                if not s3_response.get('ResponseMetadata').get('HTTPStatusCode') == 200:
                    logger.error(f'Failed to retrieve upload file for {record_metadata.get("DRB_Record ID")} to S3')
                    continue

                s3_url = f'https://{bucket}.s3.amazonaws.com/{s3_path}'
                
                publisher_backlist_record = PublisherBacklistMapping(record_metadata)
                publisher_backlist_record.applyMapping()
                
                self.add_has_part_mapping(s3_url, publisher_backlist_record.record)
                self.store_pdf_manifest(publisher_backlist_record.record)
                
                mapped_records.append(publisher_backlist_record)
            except Exception:
                logger.exception(f'Failed to process Publisher Backlist record: {record_metadata}')
        
        return mapped_records
        
    def build_filter_by_formula_parameter(self, deleted=None, full_import: bool=False, start_timestamp: datetime=None) -> str:
        if deleted:
            delete_filter = urllib.parse.quote("{DRB_Deleted} = TRUE()")
            
            return f"&filterByFormula={delete_filter}"
        
        is_not_deleted_filter = urllib.parse.quote("{DRB_Deleted} = FALSE()")
        ready_to_ingest_filter = urllib.parse.quote("{DRB_Ready to ingest} = TRUE()")

        if full_import:
            return f'&filterByFormula=AND({ready_to_ingest_filter},{is_not_deleted_filter})'
        
        if not start_timestamp:
            start_timestamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
        
        start_date_time_str = start_timestamp.strftime('%Y-%m-%d')
        is_same_date_time_filter = urllib.parse.quote(f"IS_SAME({{Last Modified}}, \"{start_date_time_str}\")")
        is_after_date_time_filter = urllib.parse.quote(f"IS_AFTER({{Last Modified}}, \"{start_date_time_str}\")")
    
        return f"&filterByFormula=AND(OR({is_same_date_time_filter}),{is_after_date_time_filter})),{ready_to_ingest_filter},{is_not_deleted_filter})"
        
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

    def add_has_part_mapping(self, s3_url: str, record: Record, is_downloadable: bool=False, is_login_limited: bool=True):
        item_no = '1'
        media_type = 'application/pdf'
        flags = {
            'catalog': False,
            'download': is_downloadable,
            'reader': False,
            'embed': False,
            'nypl_login': is_login_limited,
        }

        record.has_part.append('|'.join([item_no, s3_url, record.source, media_type, json.dumps(flags)]))

    def store_pdf_manifest(self, record: Record):
        for link in record.has_part:
            item_no, url, source, media_type, _ = link.split('|')

            if media_type == 'application/pdf':
                manifest_path = f'manifests/publisher_backlist/{source}/{record.source_id}.json'
                manifest_url = f'https://{self.file_bucket}.s3.amazonaws.com/{manifest_path}'

                manifest_json = self.generate_manifest(record, url, manifest_url)

                self.s3_manager.createManifestInS3(manifest_path, manifest_json, self.file_bucket)

                manifest_flags = {
                    'catalog': False,
                    'download': False,
                    'reader': True,
                    'embed': False,
                    **({'fulfill_limited_access': False} if 'in_copyright' in record.rights else {})
                }

                record.has_part.insert(0, '|'.join([item_no, manifest_url, source, 'application/webpub+json', json.dumps(manifest_flags)]))
                
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

    @staticmethod
    def parse_permissions(permissions: str) -> dict:
        if permissions == LimitedAccessPermissions.FULL_ACCESS.value:
            return {'is_downloadable': True, 'is_login_limited': False}
        if permissions == LimitedAccessPermissions.PARTIAL_ACCESS.value:
            return {'is_downloadable': False, 'is_login_limited': False}
        if permissions == LimitedAccessPermissions.LIMITED_DOWNLOADABLE.value:
            return {'is_downloadable': True, 'is_login_limited': True}
        else:
            return {'is_downloadable': False, 'is_login_limited': True}
