from abc import ABC, abstractmethod
import boto3
import os

from managers.db import DBManager
from models.data.interaction_event import InteractionEvent


class Aggregator(ABC):
    def __init__(self, publisher, date_range):
        self.publisher = publisher
        self.date_range = date_range
        self.s3_client = boto3.client("s3")

    @abstractmethod
    def pull_interaction_events(self) -> list[InteractionEvent]:
        return

    @abstractmethod
    def match_log_info_with_drb_data(self, log_object) -> InteractionEvent | None:
        return

    def setup_db_manager(self):
        self.db_manager = DBManager(
            user=os.environ.get("POSTGRES_USER", None),
            pswd=os.environ.get("POSTGRES_PSWD", None),
            host=os.environ.get("POSTGRES_HOST", None),
            port=os.environ.get("POSTGRES_PORT", None),
            db=os.environ.get("POSTGRES_NAME", None),
        )
        self.db_manager.generateEngine()
        self.db_manager.createSession()

    def load_batch(self, log_path, bucket_name, log_folder):
        prefix = log_path + log_folder + "/"
        paginator = self.s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=bucket_name, Prefix=prefix)
        return page_iterator

    def parse_logs_in_batch(self, batch, bucket_name) -> list:
        '''
        Pulls logs from a given S3 batch, then parses each log to see if 
        it contains an InteractionEvent (e.g. view, download, etc).
        '''
        interactions_in_batch = []

        for log_file in batch:
            if "Contents" not in log_file:
                path = self.redact_s3_path(log_file["Prefix"])
                raise S3LogParsingError(
                    f"Log files in path {path} do not exist.")
            else:
                for content in log_file["Contents"]:
                    curr_key = str(content["Key"])
                    log_object_dict = self.s3_client.get_object(
                        Bucket=bucket_name, Key=f"{curr_key}"
                    )
                    for i in log_object_dict["Body"].iter_lines():
                        log_object_dict = i.decode("utf8")
                        interaction_event = self.match_log_info_with_drb_data(
                            log_object_dict)
                        if interaction_event:
                            interactions_in_batch.append(
                                interaction_event)

        return interactions_in_batch

    def redact_s3_path(self, path):
        '''
        Used to remove sensitive data from S3 prefix before passing to error message.
        Example input = "logs/123456789/us-east-1/ump-pdf-repository/2024/1/1"
        Example output: "logs/NYPL_AWS_ID/us-east-1/ump-pdf-repository/2024/1/1"
        '''
        split_path = path.split("/")
        split_path[1] = "NYPL_AWS_ID"
        return "/".join(split_path)


class S3LogParsingError(Exception):
    def __init__(self, message=None):
        self.message = message
