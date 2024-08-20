import os
import re

from model import Edition, Item, Link
from models.aggregators.aggregator import Aggregator, UnconfiguredEnvironment
from models.data.interaction_event import InteractionEvent, InteractionType, UsageType
from model.postgres.item import ITEM_LINKS
from model.postgres.record import Record
from model.postgres.work import Work

REQUEST_REGEX = r"REST.GET.OBJECT "
FILE_ID_REGEX = r"REST.GET.OBJECT (.+pdf\s)"
TIMESTAMP_REGEX = r"\[.+\]"


class DownloadDataAggregator(Aggregator):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("DOWNLOAD_BUCKET", None)
        self.log_path = os.environ.get("DOWNLOAD_LOG_PATH", None)

        self.setup_db_manager()
        self.set_events()

    def set_events(self):
        if None in (self.bucket_name, self.log_path, self.referrer_url):
            error_message = (
                "One or more necessary environment variables not found:",             
                "Either DOWNLOAD_BUCKET, DOWNLOAD_LOG_PATH, REFERRER_URL is not set"
            )
            print(error_message)
            raise UnconfiguredEnvironment(error_message)

        self.events = self.pull_interaction_events(self.log_path, self.bucket_name)
        self.db_manager.closeConnection()

    def match_log_info_with_drb_data(self, log_object):
        match_request = re.search(REQUEST_REGEX, log_object)
        match_referrer = re.search(str(self.referrer_url), log_object)

        if match_request and match_referrer and "403 AccessDenied" not in log_object:
            match_time = re.search(TIMESTAMP_REGEX, log_object)
            match_file_id = re.search(FILE_ID_REGEX, log_object)
            link_group = match_file_id.group(1)
            
            items = self.db_manager.session.query(Item).filter(Item.source == self.publisher)

            # TODO: simplify this query, it's too nested
            for item in items:
                links = self.db_manager.session.query(Link) \
                    .join(ITEM_LINKS) \
                    .filter(ITEM_LINKS.c.item_id == item.id) \
                    .filter(Link.media_type == "application/pdf") \
                    .filter(Link.url.contains(link_group.strip())) \
                    .all()

                for link in links:
                    editions = self.db_manager.session.query(Edition).filter(Edition.id == item.edition_id)

                    for edition in editions:
                        title = edition.title
                        copyright_year, publication_year = self.pull_dates_from_edition(edition)
                        
                        records = self.db_manager.session.query(Record).filter(Record.uuid.in_(edition.dcdw_uuids))

                        for record in records:
                            book_id = (record.source_id).split("|")[0]
                            usage_type = self._determine_usage(record)
                            isbns = [identifier.split(
                                "|")[0] for identifier in record.identifiers if "isbn" in identifier]
                            
                        works = self.db_manager.session.query(Work).filter(Work.id == edition.work_id)

                        for work in works:
                            authors = [author["name"] for author in work.authors]
                            disciplines = [subject["heading"] for subject in work.subjects]

            return InteractionEvent(
                title=title,
                book_id=book_id,
                authors="; ".join(authors),
                isbns=", ".join(isbns),
                copyright_year=copyright_year,
                publication_year=publication_year,
                disciplines=", ".join(disciplines),
                country_count=None,
                usage_type=usage_type.value,
                interaction_type=InteractionType.DOWNLOAD,
                timestamp=match_time.group(0)
            )

    def _determine_usage(self, record):
        if record.has_part is not None:
            for item in record.has_part:
                _, uri, _, _, flag_string = tuple(item.split('|'))
                if "pdf" in uri:
                    flags = self.load_flags(flag_string)
                    if (("embed" in flags) and flags["embed"]) or (
                            ("reader" in flags) and flags["reader"]):
                        return UsageType.FULL_ACCESS
        return UsageType.LIMITED_ACCESS
