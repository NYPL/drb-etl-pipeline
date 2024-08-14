import re
import os

from logger import createLog
from model.postgres.edition import Edition
from model.postgres.record import Record
from model.postgres.work import Work
from models.aggregators.aggregator import Aggregator, UnconfiguredEnvironment
from models.data.interaction_event import InteractionEvent, InteractionType, UsageType
from sqlalchemy import func

# Regexes needed to parse S3 logs
FILE_ID_REGEX = r"REST.GET.OBJECT manifests/(.*?json)\s"
TIMESTAMP_REGEX = r"\[.+\]"


class ViewDataAggregator(Aggregator):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("VIEW_BUCKET", None)
        self.log_path = os.environ.get("VIEW_LOG_PATH", None)

        self.logger = createLog("view_data_aggregator")
        self.setup_db_manager()
        self.set_events()

    def set_events(self):
        if None in (self.bucket_name, self.log_path, self.referrer_url):
            error_message = (
                "One or more necessary environment variables not found:",
                "Either VIEW_BUCKET, VIEW_LOG_PATH, REFERRER_URL is not set",
            )
            self.logger.error(error_message)
            raise UnconfiguredEnvironment(error_message)

        self.events = self.pull_interaction_events(
            self.log_path, self.bucket_name)
        self.db_manager.closeConnection()

    def match_log_info_with_drb_data(self, log_object):
        """
        Check that the S3 server access log object contains a view request.
        If so, we parse out the edition title, identifier, and timestamp.
        """
        match_file_id = re.search(FILE_ID_REGEX, log_object)
        match_referrer = re.search(str(self.referrer_url), log_object)

        if match_file_id and match_referrer and "403 AccessDenied" not in log_object:
            match_time = re.search(TIMESTAMP_REGEX, log_object)
            # some record identifiers include slashes, so we only want to 
            # split at first occurrence
            file_name = match_file_id.group(1).split("/", 1)[1]
            record_id = file_name.split(".")[0]

            # manifest file name should be the same as one of the record identifiers
            for record in (
                self.db_manager.session.query(Record)
                .filter((Record.source == self.publisher))
                .filter(func.array_to_string(
                    Record.identifiers, ",").like("%"+record_id+"%"))):
                book_id = (record.source_id).split("|")[0]
                usage_type = self._determine_usage(record)
                isbns = [
                    identifier.split("|")[0]
                    for identifier in record.identifiers
                    if "isbn" in identifier
                ]

                for edition in self.db_manager.session.query(Edition).filter(
                    Edition.dcdw_uuids.contains(f"{{{record.uuid}}}")
                ):
                    title = edition.title
                    copyright_year, publication_year = self.pull_dates_from_edition(
                        edition)

                    for work in self.db_manager.session.query(Work).filter(
                        Work.id == edition.work_id
                    ):
                        authors = [author["name"] for author in work.authors]
                        disciplines = [subject["heading"]
                                       for subject in work.subjects]

                        return InteractionEvent(
                            title=title,
                            book_id=book_id,
                            authors="; ".join(authors),
                            isbns=", ".join(isbns),
                            copyright_year=copyright_year,
                            publication_year=publication_year,
                            disciplines=", ".join(disciplines),
                            usage_type=usage_type.value,
                            interaction_type=InteractionType.VIEW,
                            timestamp=match_time.group(0)
                        )

    def _determine_usage(self, record):
        if record.has_part is not None:
            for item in record.has_part:
                _, uri, _, _, flag_string = tuple(item.split("|"))
                if "manifests" in uri:
                    flags = self.load_flags(flag_string)
                    if ("nypl_login" in flags) and flags["nypl_login"]:
                        return UsageType.LIMITED_ACCESS
                    if (("embed" in flags) and flags["embed"]) or (
                        ("reader" in flags) and flags["reader"]
                    ):
                        if ("download" in flags) and flags["download"]:
                            return UsageType.FULL_ACCESS

        return UsageType.VIEW_ONLY_NO_DOWNLOAD_ACCESS