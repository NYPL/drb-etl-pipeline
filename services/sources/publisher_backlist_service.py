from datetime import datetime, timedelta, timezone
import os
import requests
import json
import urllib.parse
from typing import Optional
from model import Record, Work, Edition, Item, Link

from logger import create_log
from mappings.publisher_backlist import PublisherBacklistMapping
from managers import S3Manager, WebpubManifest
from services.ssm_service import get_parameter
from services.google_drive_service import get_drive_file, id_from_url, get_file_metadata
from .source_service import SourceService
from managers import DBManager, ElasticsearchManager
from elasticsearch_dsl import Search, Q

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"

class PublisherBacklistService(SourceService):
    def __init__(self):

        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.s3_bucket = os.environ['FILE_BUCKET']
<<<<<<< HEAD
        self.manifest_prefix = 'manifests/publisher_backlist'
        self.title_prefix = 'titles/publisher_backlist'

        if os.environ['ENVIRONMENT'] == 'production':
            self.airtable_auth_token = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/airtable/pub-backlist/api-key')
        else:
            self.airtable_auth_token = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/airtable/pub-backlist/api-key')
=======
        self.prefix = 'manifests/publisher_backlist'
        self.db_manager = DBManager()
        self.db_manager.generateEngine()
        self.es_manager = ElasticsearchManager()
        self.es_manager.createElasticConnection()
        
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)
>>>>>>> Drive-refactor-as-class

    def delete_records(
        self,
        limit: Optional[int]=None
    ):
        filter_by_formula = self.build_filter_by_formula_parameter(deleted=True)
        
        array_json_records = self.get_records_array(limit, filter_by_formula)

        for json_dict in array_json_records:
            if json_dict['records']:
                for records_value in json_dict['records']:
                    if records_value['fields']:
                        record_metadata_dict = records_value['fields']
                        self.delete_manifest(self.db_manager, record_metadata_dict)
                        self.delete_work(record_metadata_dict)
        
    def delete_manifest(self, record_metadata_dict):
        self.db_manager.createSession()
        try:
            record = self.db_manager.session.query(Record).filter(Record.source_id == record_metadata_dict['DRB Record_ID']).first()
            if record:
                key_name = self.get_metadata_file_name(record, record_metadata_dict)
                self.s3_manager.s3Client.delete_object(Bucket= self.s3_bucket, Key= key_name)
        except Exception:
            logger.exception(f'Failed to delete manifest for record: {record.source_id}')
        finally:
            self.db_manager.session.close()

    def delete_work(self, record_metadata_dict):
        self.db_manager.createSession()
        record = self.db_manager.session.query(Record).filter(Record.source_id == record_metadata_dict['DRB Record_ID']).first()

        try:
            if record:
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
        except Exception:
            logger.exception('Work/Edition does not exist or failed to delete work: {work.id}')
        finally:
            self.db_manager.session.close()
            
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
            
    def get_metadata_file_name(self, record, record_metadata_dict):
        key_format = f"{self.manifest_prefix}{record.source}"

        if record_metadata_dict['File ID 1']:
            file_title = record_metadata_dict['File ID 1']
        elif record_metadata_dict['File ID 2']:
            file_title = record_metadata_dict['File ID 2']
        elif record_metadata_dict['Hathi ID']:
            file_title = record_metadata_dict['Hathi ID']
        else:
            raise Exception
        
        key_name = f'{key_format}{file_title}.json'
        return key_name

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
                    file_id = f'{id_from_url(record_metadata_dict["DRB_File Location"])}'
                    file_name = get_file_metadata(file_id).get("name")
                    file = get_drive_file(file_id)
                    import sys
                    print(f'how big file? {sys.getsizeof(file)}')
                    if not file:
                        logger.warn(f'Could not retrieve file for {record_metadata_dict["id"]}, skipping')
                        continue
                    file_put = self.s3_manager.putObjectInBucket(file.getvalue(), f'{self.title_prefix}/{record_metadata_dict["Publisher (from Projects)"][0]}/{file_name}', self.s3_bucket)
                    pub_backlist_record = PublisherBacklistMapping(record_metadata_dict)
                    pub_backlist_record.applyMapping()
                    self.add_has_part_mapping(pub_backlist_record.record)
                    self.store_pdf_manifest(pub_backlist_record.record)
                    complete_records.append(pub_backlist_record)
                except Exception:
                    logger.exception(f'Failed to process Publisher Backlist record: {records_value}')
        return complete_records
    
    def get_records_json(self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[dict]:
        if offset == None:
            limit = 100
<<<<<<< HEAD

        filter_by_formula = self.build_filter_by_formula_parameter(deleted=False, full_import=full_import, start_timestamp=start_timestamp)
=======
            
        limit = offset
        
        filter_by_formula = self.build_filter_by_formula_parameter(deleted=False, full_import=None, start_timestamp=None)
                
>>>>>>> Drive-refactor-as-class
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
    
    def add_has_part_mapping(self, record):

        #GOOGLE DRIVE API CALL TO GET PDF/EPUB FILES

        try:
            if 'in_copyright' in record.rights:
                link_string = '|'.join([
                    '1',
                    #LINK TO PDF/EPUB,
                    record.source,
                    'application/pdf',
                    '{"catalog": false, "download": true, "reader": false, "embed": false, "nypl_login": true}'
                ])
                record.has_part.append(link_string)

            if 'public_domain' in record.rights:
                link_string = '|'.join([
                    '1',
                    #LINK TO PDF/EPUB,
                    record.source,
                    'application/pdf',
                    '{"catalog": false, "download": true, "reader": false, "embed": false}'
                ])
                record.has_part.append(link_string)

        except Exception as e:
            logger.exception(e)

    def store_pdf_manifest(self, record):
        for link in record.has_part:
            item_no, url, source, media_type, flags = link.split('|')

            if media_type == 'application/pdf':
                record_id = record.identifiers[0].split('|')[0]
                manifest_path = f'{self.manifest_prefix}/{source}/{record_id}.json'
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
