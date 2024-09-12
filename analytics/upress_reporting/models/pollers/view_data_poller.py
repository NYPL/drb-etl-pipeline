import re
import os

from model.postgres.edition import Edition
from model.postgres.record import Record
from model.postgres.work import Work
from models.pollers.poller import Poller
from models.data.interaction_event import InteractionEvent, InteractionType, UsageType
from sqlalchemy import func

FILE_ID_REGEX = r"REST.GET.OBJECT manifests/(.*?json)\s"
TIMESTAMP_REGEX = r"\[.+\]"
IP_REGEX = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"


class ViewDataPoller(Poller):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("VIEW_BUCKET", None)
        self.log_path = os.environ.get("VIEW_LOG_PATH", None)

        self.setup_db_manager()
        self.get_events(self.bucket_name, self.log_path, FILE_ID_REGEX)
        self.db_manager.closeConnection()

    def match_log_info_with_drb_data(self, log_object):
        match_file_id = re.search(FILE_ID_REGEX, log_object)
        # match_referrer = re.search(str(self.referrer_url), log_object)

        # if not match_file_id or not match_referrer or "403 AccessDenied" in log_object:
        #     return None

        match_time = re.search(TIMESTAMP_REGEX, log_object)
        match_ip = re.search(IP_REGEX, log_object)
        file_name = match_file_id.group(1).split("/", 1)[1]
        record_id = file_name.split(".")[0]
        record = self.db_manager.session.query(Record) \
            .filter((Record.source == self.publisher)) \
            .filter(func.array_to_string(Record.identifiers, ",").like("%"+record_id+"%")) \
            .first()

        if record is None:
            return None

        usage_type = self._determine_usage(record)
        isbns = [identifier.split("|")[0] for identifier in record.identifiers if "isbn" in identifier]
        oclc_numbers = [identifier.split("|")[0] for identifier in record.identifiers if "oclc" in identifier]

        edition = self.db_manager.session.query(Edition).filter(
            Edition.dcdw_uuids.contains(f"{{{record.uuid}}}")).first()

        book_id = f'{self.referrer_url}edition/{edition.id}'
        title = edition.title
        publication_year = self.pull_publication_year(edition)

        authors = [author.split('|')[0] for author in record.authors]
        disciplines = [subject.split('|')[0] for subject in record.subjects or []]

        return InteractionEvent(
            country=self.map_ip_to_country(match_ip.group()),
            title=title,
            book_id=book_id,
            authors="; ".join(authors),
            isbns=", ".join(isbns),
            oclc_numbers=", ".join(oclc_numbers),
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

        return UsageType.VIEW_ACCESS
