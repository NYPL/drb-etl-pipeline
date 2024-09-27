import boto3
import geocoder
import json
import os
import pandas
import re

from abc import ABC, abstractmethod
from helpers import aggregate_logs
from managers.db import DBManager
from models.data.interaction_event import InteractionEvent, UsageType

IP_REGEX = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"


class Poller(ABC):
    def __init__(self, publisher, date_range):
        self.publisher = publisher
        self.date_range = date_range
        self.s3_client = boto3.client("s3")
        self.referrer_url = os.environ.get("REFERRER_URL", None)

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

    def get_events(self, bucket_name, log_path, regex):
        if None in (bucket_name, log_path, self.referrer_url):
            error_message = (
                "One or more necessary environment variables not found:",
                "Either DOWNLOAD_BUCKET, DOWNLOAD_LOG_PATH, REFERRER_URL is not set"
            )
            print(error_message)
            raise UnconfiguredEnvironmentError(error_message)

        self.events = self.pull_interaction_events_from_logs(
            log_path, bucket_name, regex)

    def pull_interaction_events_from_logs(self, log_path, bucket_name, regex) -> list[InteractionEvent]:
        events = []
        today = pandas.Timestamp.today()

        aggregate_logs.aggregate_logs_in_period(self.date_range, bucket_name,
                                                log_path, regex, self.referrer_url)

        for date in self.date_range:
            if date > today:
                print("No logs exist past today's date: ",
                      today.strftime("%b %d, %Y"))
                break

            file_name = f"analytics/upress_reporting/log_files/{
                bucket_name}/{date.strftime('%Y/%m/%d')}/aggregated_log"
            events_per_day = self.parse_log_file(file_name)
            events.extend(events_per_day)

        return events

    def parse_log_file(self, file_name):
        interactions_in_batch = []

        with open(file_name, "r") as aggregated_log_file:
            for line in aggregated_log_file:
                interaction_event = self.match_log_info_with_drb_data(line)

                if interaction_event:
                    interactions_in_batch.append(interaction_event)

        return interactions_in_batch

    def map_ip_to_country(self, ip) -> str | None:
        if re.match(IP_REGEX, ip):
            geocoded_ip = geocoder.ip(ip)
            return geocoded_ip.country

        return None

    def pull_publication_year(self, edition):
        for date in edition.dates:
            if "publication" in date["type"]:
                return date["date"]

        return None

    def load_flags(self, flag_string):
        try:
            flags = json.loads(flag_string)
            return flags if isinstance(flags, dict) else {}
        except json.decoder.JSONDecodeError as e:
            raise S3LogParsingError(e.msg)

    def determine_usage(self, record):
        if record.has_part:
            flags = [self.load_flags(tuple(link.split("|"))[4])
                     for link in record.has_part]

            if any(flag.get('nypl_login', False) for flag in flags):
                return UsageType.LIMITED_ACCESS

            has_read_flag = any(flag.get('embed', False) or flag.get(
                'reader', False) for flag in flags)
            has_download_flag = any(flag.get('download', False)
                                    for flag in flags)

            if has_read_flag and has_download_flag:
                return UsageType.FULL_ACCESS

        return UsageType.VIEW_ACCESS

    def _redact_s3_path(self, path):
        split_path = path.split("/")
        split_path[1] = "NYPL_AWS_ID"
        return "/".join(split_path)


class S3LogParsingError(Exception):
    def __init__(self, message=None):
        self.message = message


class UnconfiguredEnvironmentError(Exception):
    def __init__(self, message=None):
        self.message = message
