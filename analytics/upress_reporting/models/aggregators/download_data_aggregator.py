import json
import boto3
import os
import re

from logger import createLog
from model import Edition, Item, Link
from models.aggregators.aggregator import Aggregator
from models.data.interaction_event import InteractionEvent, InteractionType, UsageType
from model.postgres.item import ITEM_LINKS
from managers import DBManager
from model.postgres.record import Record
from model.postgres.work import Work

# Regexes needed to parse S3 logs
REQUEST_REGEX = r"REST.GET.OBJECT "
# File ID includes the file name for the pdf object
FILE_ID_REGEX = r"REST.GET.OBJECT (.+pdf\s)"
TIMESTAMP_REGEX = r"\[.+\]"
REFERRER_REGEX = r"https://drb-qa.nypl.org/"


class DownloadDataAggregator(Aggregator):
    """
    Parses S3 download logs and generates list of DownloadEvents, each corresponding 
    to a single download request.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("DOWNLOAD_BUCKET", None)
        self.log_path = os.environ.get("DOWNLOAD_LOG_PATH", None)

        self.logger = createLog("download_data_aggregator")
        self.setup_db_manager()

    def pull_interaction_events(self):
        '''
        Returns list of download InteractionEvents in a given reporting period.
        '''
        download_events = []

        for date in self.date_range:
            folder_name = date.strftime("%Y/%m/%d")
            batch = self.load_batch(self.log_path, self.bucket_name, 
                                    folder_name)
            downloads_per_day = self.parse_logs_in_batch(batch, self.bucket_name)
            download_events.extend(downloads_per_day)
        
        self.db_manager.closeConnection()

        return download_events

    def match_log_info_with_drb_data(self, log_object):
        '''
        Check that the S3 server access log object contains a download request. 
        If so, we parse out the edition title, identifier, and timestamp.
        '''
        matchRequest = re.search(REQUEST_REGEX, log_object)
        matchReferrer = re.search(REFERRER_REGEX, log_object)

        if matchRequest and matchReferrer and "403 AccessDenied" not in log_object:
            match_time = re.search(TIMESTAMP_REGEX, log_object)
            match_file_id = re.search(FILE_ID_REGEX, log_object)
            link_group = match_file_id.group(1)

            # TODO: simplify this query, it's too nested
            for item in self.db_manager.session.query(Item).filter(
                    Item.source == self.publisher):
                for link in (
                    self.db_manager.session.query(Link)
                    .join(ITEM_LINKS)
                    .filter(ITEM_LINKS.c.item_id == item.id)
                    .filter(Link.media_type == "application/pdf")
                    .filter(Link.url.contains(link_group.strip()))
                        .all()):
                    for edition in self.db_manager.session.query(Edition).filter(
                            Edition.id == item.edition_id):
                        title = edition.title
                        copyright_year = self._pull_copyright_year(edition)

                        for record in self.db_manager.session.query(Record).filter(
                                Record.uuid.in_(edition.dcdw_uuids)):
                            book_id = (record.source_id).split("|")[0]
                            usage_type = self._determine_usage(record)
                            isbns = [identifier.split(
                                "|")[0] for identifier in record.identifiers if "isbn" in identifier]
                            eisbns = [identifier.split(
                                "|")[0] for identifier in record.identifiers if "eisbn" in identifier]

                        for work in self.db_manager.session.query(Work).filter(
                                Work.id == edition.work_id):
                            authors = [author["name"]
                                       for author in work.authors]
                            disciplines = [subject["heading"]
                                           for subject in work.subjects]

            return InteractionEvent(
                title=title,
                book_id=book_id,
                authors=authors,
                isbns=isbns,
                eisbns=eisbns,
                copyright_year=copyright_year,
                disciplines=disciplines,
                usage_type=usage_type,
                interaction_type=InteractionType.DOWNLOAD,
                timestamp=match_time.group(0)
            )

    def _pull_copyright_year(self, edition):
        for date in edition.dates:
            if "copyright" in date["type"]:
                return date["date"]

        return None

    def _determine_usage(self, record):
        if record.has_part is not None:
            for item in record.has_part:
                _, uri, _, _, flag_string = tuple(item.split('|'))
                if "pdf" in uri:
                    flags = self._load_flags(flag_string)
                    if (("embed" in flags.keys()) and (flags["embed"] is True)) or (
                        ("reader" in flags.keys()) and (flags["reader"] is True)):
                        return UsageType.FULL_ACCESS
        return UsageType.LIMITED_ACCESS

    def _load_flags(self, flag_string):
        try:
            flags = json.loads(flag_string)
            return flags if isinstance(flags, dict) else {}
        except json.decoder.JSONDecodeError:
            self.logger.error(
                "Unable to parse nypl_login flags...")
        return {}
