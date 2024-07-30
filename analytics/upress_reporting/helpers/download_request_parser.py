import os
import boto3
import numpy
import re
import shutil

from logger import createLog
from model import Edition, Item, Link
from model.postgres.item import ITEM_LINKS
from managers import DBManager

# Regexes needed to parse S3 logs
REQUEST_REGEX = r"REST.GET.OBJECT "
# File ID includes the file name for the pdf object
FILE_ID_REGEX = r"REST.GET.OBJECT (.+pdf\s)"
TIMESTAMP_REGEX = r"\[.+\]"
REFERRER_REGEX = r"https://drb-qa.nypl.org/"


class DownloadRequestParser:
    """
    Parses S3 download logs and generates CSVs with all download requests
    for each day. All CSVs are stored locally in "download_csvs" directory.
    """

    def __init__(self, publisher, date_range):
        self.publisher = publisher
        self.date_range = date_range

        self.s3_client = boto3.client("s3")
        self.bucket_name = os.environ.get("DOWNLOAD_BUCKET", None)
        self.log_path = os.environ.get("DOWNLOAD_LOG_PATH", None)

        self._setup_db_manager()
        self.logger = createLog("download_request_parser")

    def generate_csv_files(self):
        csv_directory = "download_csvs"

        for date in self.date_range:
            folder_name = date.strftime("%Y/%m/%d")
            new_dir = f"{csv_directory}/{folder_name}"
            # Delete any old files and make a new directory before beginning
            if os.path.exists(new_dir):
                shutil.rmtree(new_dir)
            os.makedirs(new_dir)

            batch = self._load_batch(folder_name)
            downloads_per_day = self._parse_logs(batch)
            numpy_download_array = numpy.asarray(downloads_per_day)
            numpy.savetxt(f"{new_dir}/{date.day}.csv",
                          numpy_download_array,
                          delimiter=",",
                          fmt="%s")

        self.db_manager.session.close()

    def _setup_db_manager(self):
        self.db_manager = DBManager(
            user=os.environ.get("POSTGRES_USER", None),
            pswd=os.environ.get("POSTGRES_PSWD", None),
            host=os.environ.get("POSTGRES_HOST", None),
            port=os.environ.get("POSTGRES_PORT", None),
            db=os.environ.get("POSTGRES_NAME", None),
        )
        self.db_manager.generateEngine()
        self.db_manager.createSession()

    def _load_batch(self, log_folder):
        prefix = self.log_path + log_folder + "/"
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.bucket_name, Prefix=prefix)
        return page_iterator

    def _parse_logs(self, batch):
        '''
        The edition title, identifier, and timestamp are parsed out of the
        S3 server access log files for UMP download requests.
        '''
        # initial array contains headers for CSV
        ump_downloads_array = [["title", "timeStamp", "identifier"]]

        for log_file in batch:
            if "Contents" not in log_file:
                path = self._redact_s3_path(log_file["Prefix"])
                raise DownloadParsingError(
                    f"Log files in path {path} do not exist.")
            else:
                for c in log_file["Contents"]:
                    curr_key = str(c["Key"])
                    # log_object is a dict type
                    log_object = self.s3_client.get_object(
                        Bucket=self.bucket_name, Key=f"{curr_key}"
                    )
                    for i in log_object["Body"].iter_lines():
                        log_object = i.decode("utf8")
                        parse_tuple = self._match_log_info_with_frbr_data(
                            log_object)
                        if parse_tuple:
                            ump_downloads_array.append(parse_tuple)

        return ump_downloads_array

    def _redact_s3_path(self, path):
        '''
        Used to remove sensitive data from S3 prefix before passing to error message.
        Example input = "logs/123456789/us-east-1/ump-pdf-repository/2024/1/1"
        Example output: "logs/NYPL_AWS_ID/us-east-1/ump-pdf-repository/2024/1/1"
        '''
        split_path = path.split("/")
        split_path[1] = "NYPL_AWS_ID"
        return "/".join(split_path)

    def _match_log_info_with_frbr_data(self, log_object):
        matchRequest = re.search(REQUEST_REGEX, log_object)
        matchReferrer = re.search(REFERRER_REGEX, log_object)

        if matchRequest and matchReferrer and "403 AccessDenied" not in log_object:
            match_time = re.search(TIMESTAMP_REGEX, log_object)
            match_file_id = re.search(FILE_ID_REGEX, log_object)
            link_group = match_file_id.group(1)
            title_parse = ""
            id_parse = None

            for item in self.db_manager.session.query(Item).filter(
                Item.source == self.publisher
            ):
                for link in (
                    self.db_manager.session.query(Link)
                    .join(ITEM_LINKS)
                    .filter(ITEM_LINKS.c.item_id == item.id)
                    .filter(Link.media_type == "application/pdf")
                    .filter(Link.url.contains(link_group.strip()))
                    .all()
                ):
                    item_edit_id = item.edition_id
                    for edit in self.db_manager.session.query(Edition).filter(
                        Edition.id == item_edit_id
                    ):
                        title_parse = edit.title
                        id_parse = edit.id

            return [title_parse, match_time.group(0), id_parse]


class DownloadParsingError(Exception):
    def __init__(self, message=None):
        self.message = message
