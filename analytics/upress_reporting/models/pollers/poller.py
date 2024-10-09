import geocoder
import json
import os
import pandas
import re

from models.data.interaction_event import InteractionEvent, InteractionType, UsageType

IP_REGEX = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"
REQUEST_REGEX = r"REST.GET.OBJECT "
TIMESTAMP_REGEX = r"\[.+\]"


class Poller():
    def __init__(self, date_range, reporting_data,
                 file_id_regex, bucket_name, interaction_type):
        self.date_range = date_range
        self.reporting_data = reporting_data
        self.file_id_regex = file_id_regex
        self.bucket_name = bucket_name
        self.interaction_type = interaction_type

        self.referrer_url = os.environ.get("REFERRER_URL", None)
        self.get_events(self.bucket_name)

    def get_events(self, bucket_name):
        self.events = self._pull_interaction_events_from_logs(
            bucket_name)

    def _pull_interaction_events_from_logs(self, bucket_name) -> list[InteractionEvent]:
        events = []
        today = pandas.Timestamp.today()

        for date in self.date_range:
            if date > today:
                print("No logs exist past today's date: ",
                      today.strftime("%b %d, %Y"))
                break

            formatted_date = date.strftime('%Y/%m/%d')
            file_name = f"analytics/upress_reporting/log_files/{
                bucket_name}/{formatted_date}/aggregated_log"

            if not os.path.isfile(file_name):
                print(f"There are no logs for {
                      formatted_date}. Attempting to access logs beyond this date...")
                continue

            events_per_day = self._parse_aggregated_log_file(file_name)
            events.extend(events_per_day)

        return events

    def _parse_aggregated_log_file(self, file_name):
        interactions_in_batch = []

        with open(file_name, "r") as aggregated_log_file:
            for line in aggregated_log_file:
                interaction_event = self._match_log_info_with_drb_data(line)

                if interaction_event:
                    interactions_in_batch.append(interaction_event)

        return interactions_in_batch

    def _match_log_info_with_drb_data(self, log_object) -> InteractionEvent | None:
        match_request = re.search(REQUEST_REGEX, log_object)
        match_referrer = re.search(str(self.referrer_url), log_object)

        if not match_request or not match_referrer or "403 AccessDenied" in log_object:
            return None

        match_file_id = re.search(self.file_id_regex, log_object)
        match_time = re.search(TIMESTAMP_REGEX, log_object)
        match_ip = re.search(IP_REGEX, log_object)

        if self.interaction_type == InteractionType.VIEW:
            file_name = match_file_id.group(1).split("/", 1)[1]
        else:
            file_name = match_file_id.group(1)

        drb_data_match = [
            data for key, data in self.reporting_data.items() if file_name in key.lower()]

        if not drb_data_match or len(drb_data_match) < 1:
            return None

        match_data = drb_data_match[0]

        title = match_data.title
        publication_year = self._pull_publication_year(match_data)

        book_id = f'{self.referrer_url}edition/{match_data.id}'
        usage_type = self._determine_usage(match_data)
        isbns = [identifier.split(
            "|")[0] for identifier in match_data.identifiers if "isbn" in identifier]
        oclc_numbers = [identifier.split(
            "|")[0] for identifier in match_data.identifiers if "oclc" in identifier]

        authors = [author.split('|')[0] for author in match_data.authors]
        disciplines = [subject.split('|')[0]
                       for subject in match_data.subjects or []]

        return InteractionEvent(
            country=self._map_ip_to_country(match_ip.group()),
            title=title,
            book_id=book_id,
            authors="; ".join(authors),
            isbns=", ".join(isbns),
            oclc_numbers=", ".join(oclc_numbers),
            publication_year=publication_year,
            disciplines=", ".join(disciplines),
            usage_type=usage_type.value,
            interaction_type=InteractionType.DOWNLOAD,
            timestamp=match_time[0]
        )

    def _map_ip_to_country(self, ip) -> str | None:
        if re.match(IP_REGEX, ip):
            geocoded_ip = geocoder.ip(ip)
            return geocoded_ip.country
        return None

    def _pull_publication_year(self, edition):
        for date in edition.dates:
            if "publication" in date["type"]:
                return date["date"]
        return None

    def _determine_usage(self, match_data):
        if match_data.has_part:
            flags = [self._load_flags(tuple(link.split("|"))[4])
                     for link in match_data.has_part]

            if any(flag.get('nypl_login', False) for flag in flags):
                return UsageType.LIMITED_ACCESS

            has_read_flag = any(flag.get('embed', False) or flag.get(
                'reader', False) for flag in flags)
            has_download_flag = any(flag.get('download', False)
                                    for flag in flags)

            if has_read_flag and has_download_flag:
                return UsageType.FULL_ACCESS

        return UsageType.VIEW_ACCESS

    def _load_flags(self, flag_string):
        try:
            flags = json.loads(flag_string)
            return flags if isinstance(flags, dict) else {}
        except json.decoder.JSONDecodeError as e:
            raise S3LogParsingError(e.msg)

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
