from datetime import datetime
import os
import boto3
import requests
import urllib.parse
from enum import Enum
from typing import Optional
from model import Record, Work, Edition, Item
from sqlalchemy.orm import joinedload

from digital_assets import get_stored_file_url
from logger import create_log
from mappings.publisher_backlist import PublisherBacklistMapping
from managers import S3Manager
from services.ssm_service import SSMService
from services.google_drive_service import GoogleDriveService
from .source_service import SourceService
from managers import DBManager, ElasticsearchManager
from model import FileFlags, Part

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"

SOURCE_FIELD = "Project Name (from Project)"


class LimitedAccessPermissions(Enum):
    FULL_ACCESS = "Full access"
    PARTIAL_ACCESS = "Partial access/read only/no download/no login"
    LIMITED_DOWNLOADABLE = "Limited access/login for read & download"
    LIMITED_WITHOUT_DOWNLOAD = "Limited access/login for read/no download"


class PublisherBacklistService(SourceService):
    def __init__(self):
        self.s3_manager = S3Manager()
        self.s3_manager.createS3Client()
        self.title_prefix = "titles/publisher_backlist"
        self.file_bucket = os.environ["FILE_BUCKET"]
        self.limited_file_bucket = (
            f'drb-files-limited-{os.environ.get("ENVIRONMENT", "qa")}'
        )

        self.drive_service = GoogleDriveService()

        self.db_manager = DBManager()
        self.db_manager.generate_engine()

        self.es_manager = ElasticsearchManager()
        self.es_manager.create_elastic_connection()

        self.ssm_service = SSMService()
        self.airtable_auth_token = self.ssm_service.get_parameter(
            "airtable/pub-backlist/api-key"
        )

    def delete_records(self):
        records = self.get_publisher_backlist_records(deleted=True)

        self.db_manager.create_session()

        for record in records:
            record_metadata = record.get("fields")

            if not record_metadata:
                continue

            record = (
                self.db_manager.session.query(Record)
                .filter(Record.source_id == record_metadata["DRB_Record ID"])
                .first()
            )

            if not record:
                continue

            try:
                self.delete_record_digital_assets(record)
                self.delete_record_data(record)
            except:
                logger.exception(f"Failed to delete record: {record.id}")

        self.db_manager.close_connection()

    def delete_record_digital_assets(self, record: Record):
        for part in record.has_part:
            _, link, *_ = part.split("|")
            url = urllib.parse.urlparse(link)
            bucket_name = url.hostname.split(".")[0]
            file_path = url.path.lstrip("/")

            self.s3_manager.s3Client.delete_object(Bucket=bucket_name, Key=file_path)

    def delete_record_data(self, record: Record):
        items = (
            self.db_manager.session.query(Item)
            .filter(Item.record_id == record.id)
            .all()
        )
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
                .options(joinedload(Edition.items))
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
                .options(joinedload(Work.editions))
                .filter(Work.id == work_id)
                .first()
            )
            work_ids_to_uuids[work.id] = work.uuid

            if work and not work.editions:
                self.db_manager.session.delete(work)

                self.es_manager.client.delete(
                    index=os.environ["ELASTICSEARCH_INDEX"], id=work.uuid
                )

                deleted_work_ids.add(work_id)

        self.db_manager.session.commit()

        for edition_id, work_id in deleted_edition_ids.items():
            if work_id not in deleted_work_ids:
                work_uuid = work_ids_to_uuids[work_id]
                work_document = self.es_manager.client.get(
                    index=os.environ["ELASTICSEARCH_INDEX"], id=work_uuid
                )
                editions = work_document["_source"].get("editions", [])

                updated_editions = [
                    edition for edition in editions if edition.get("id") != edition_id
                ]
                work_document["_source"]["editions"] = updated_editions

                self.es_manager.client.index(
                    index=os.environ["ELASTICSEARCH_INDEX"],
                    id=work_uuid,
                    body=work_document["_source"],
                )

    def get_records(
        self,
        start_timestamp: datetime = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[PublisherBacklistMapping]:
        records = self.get_publisher_backlist_records(
            deleted=False, start_timestamp=start_timestamp, offset=offset, limit=limit
        )
        mapped_records = []

        for record in records:
            try:
                record_metadata = record.get("fields")
                record_permissions = self.parse_permissions(
                    record_metadata.get("Access type in DRB (from Access types)")[0]
                )

                publisher_backlist_record = PublisherBacklistMapping(record_metadata)
                publisher_backlist_record.applyMapping()

                try:
                    file_url = self.download_file_from_location(
                        record_metadata,
                        record_permissions,
                        publisher_backlist_record.record,
                    )
                    if not file_url:
                        continue
                except Exception:
                    logger.exception(f"Failed to download file for {record}")
                    continue

                publisher_backlist_record.record.has_part.append(
                    str(
                        Part(
                            index=1,
                            url=file_url,
                            source=publisher_backlist_record.record.source,
                            file_type="application/pdf",
                            flags=str(
                                FileFlags(
                                    download=record_permissions["is_downloadable"],
                                    nypl_login=record_permissions["requires_login"],
                                )
                            ),
                        )
                    )
                )
                self.s3_manager.store_pdf_manifest(
                    publisher_backlist_record.record,
                    self.file_bucket,
                    flags=FileFlags(
                        reader=True, nypl_login=record_permissions["requires_login"]
                    ),
                    path="publisher_backlist",
                )
                mapped_records.append(publisher_backlist_record)
            except Exception:
                logger.exception(
                    f"Failed to process Publisher Backlist record: {record_metadata}"
                )

        return mapped_records
    
    def download_file_from_location(self, record_metadata: dict, record_permissions: dict, record: Record) -> str:
        file_location = record_metadata.get('DRB_File Location')
        destination_file_bucket = os.environ.get("FILE_BUCKET", "drb-files-local")

        if not file_location:
            hath_identifier = next(
                (
                    identifier
                    for identifier in record.identifiers
                    if identifier.endswith("hathi")
                ),
                None,
            )

            if hath_identifier is not None:
                hathi_id = hath_identifier.split('|')[0]


                try:
                    self.s3_manager.s3Client.head_object(Bucket=destination_file_bucket, Key=f'titles/publisher_backlist/Schomburg/{hathi_id}/{hathi_id}.pdf')
                    logger.exception(f'PDF already exists at key: titles/publisher_backlist/Schomburg/{hathi_id}/{hathi_id}.pdf')
                    return None
                except Exception:
                    logger.exception(f'PDF does not exist at key: titles/publisher_backlist/Schomburg/{hathi_id}/{hathi_id}.pdf')

                try:
                    pdf_bucket = os.environ["PDF_BUCKET"]
                    self.s3_manager.s3Client.head_object(
                        Bucket=pdf_bucket, Key=f"tagged_pdfs/{hathi_id}.pdf"
                    )
                except Exception:
                    logger.exception("PDF object does not exist")
                    raise Exception

                source_bucket_key = {
                    "Bucket": pdf_bucket,
                    "Key": f"tagged_pdfs/{hathi_id}.pdf",
                }
                try:
                    extra_args = {
                        'ACL': 'public-read'
                    }
                    self.s3_manager.s3Client.copy(
                        source_bucket_key,
                        destination_file_bucket,
                        f'titles/publisher_backlist/Schomburg/{hathi_id}/{hathi_id}.pdf',
                        extra_args
                    )
                except Exception:
                    logger.exception("Error during copy response")

                manifest_url = get_stored_file_url(storage_name=destination_file_bucket, file_path=f'titles/publisher_backlist/Schomburg/{hathi_id}/{hathi_id}.pdf')
                return manifest_url

            raise Exception(f"Unable to get file for {record}")

        file_id = f"{self.drive_service.id_from_url(file_location)}"
        file_name = self.drive_service.get_file_metadata(file_id).get("name")
        file = self.drive_service.get_drive_file(file_id)

        if not file:
            raise Exception(f"Unable to get file for: {record}")

        bucket = (
            self.file_bucket
            if not record_permissions["requires_login"]
            else self.limited_file_bucket
        )
        file_path = (
            f"{self.title_prefix}/{record_metadata[SOURCE_FIELD][0]}/{file_name}"
        )
        self.s3_manager.putObjectInBucket(file.getvalue(), file_path, bucket)

        return get_stored_file_url(storage_name=bucket, file_path=file_path)

    def build_filter_by_formula_parameter(
        self, deleted=None, start_timestamp: Optional[datetime] = None
    ) -> str:
        if deleted:
            delete_filter = urllib.parse.quote("{DRB_Deleted} = TRUE()")

            return f"&filterByFormula={delete_filter}"

        is_not_deleted_filter = urllib.parse.quote("{DRB_Deleted} = FALSE()")
        ready_to_ingest_filter = urllib.parse.quote("{DRB_Ready to ingest} = TRUE()")

        if not start_timestamp:
            return f"&filterByFormula=AND({ready_to_ingest_filter},{is_not_deleted_filter})"

        start_date_time_str = start_timestamp.strftime("%Y-%m-%d")
        is_same_date_time_filter = urllib.parse.quote(
            f'IS_SAME({{Last Modified}}, "{start_date_time_str}")'
        )
        is_after_date_time_filter = urllib.parse.quote(
            f'IS_AFTER({{Last Modified}}, "{start_date_time_str}")'
        )

        return f"&filterByFormula=AND(OR({is_same_date_time_filter}),{is_after_date_time_filter})),{ready_to_ingest_filter},{is_not_deleted_filter})"

    def get_publisher_backlist_records(
        self,
        deleted: bool = False,
        start_timestamp: datetime = None,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        filter_by_formula = self.build_filter_by_formula_parameter(
            deleted=deleted, start_timestamp=start_timestamp
        )
        url = f"{BASE_URL}&pageSize={limit}{filter_by_formula}"
        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}
        publisher_backlist_records = []

        records_response = requests.get(url, headers=headers)
        records_response_json = records_response.json()

        publisher_backlist_records.extend(records_response_json.get("records", []))

        while "offset" in records_response_json:
            next_page_url = url + f"&offset={records_response_json['offset']}"

            records_response = requests.get(next_page_url, headers=headers)
            records_response_json = records_response.json()

            publisher_backlist_records.extend(records_response_json.get("records", []))
        return publisher_backlist_records

    @staticmethod
    def parse_permissions(permissions: str) -> dict:
        if permissions == LimitedAccessPermissions.FULL_ACCESS.value:
            return {"is_downloadable": True, "requires_login": False}
        if permissions == LimitedAccessPermissions.PARTIAL_ACCESS.value:
            return {"is_downloadable": False, "requires_login": False}
        if permissions == LimitedAccessPermissions.LIMITED_DOWNLOADABLE.value:
            return {"is_downloadable": True, "requires_login": True}
        else:
            return {"is_downloadable": False, "requires_login": True}
