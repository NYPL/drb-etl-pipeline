import os
import re
import time

from model import Edition, Item, Link
from models.pollers.poller import Poller
from models.data.interaction_event import InteractionEvent, InteractionType, UsageType
from model.postgres.item import ITEM_LINKS
from model.postgres.record import Record
from model.postgres.work import Work

REQUEST_REGEX = r"REST.GET.OBJECT "
FILE_ID_REGEX = r"REST.GET.OBJECT (.+pdf\s)"
TIMESTAMP_REGEX = r"\[.+\]"
IP_REGEX = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"


class DownloadDataPoller(Poller):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("DOWNLOAD_BUCKET", None)
        self.log_path = os.environ.get("DOWNLOAD_LOG_PATH", None)

        self.setup_db_manager()

        self.set_items()
        self.get_events(self.bucket_name, self.log_path, FILE_ID_REGEX)
        self.db_manager.closeConnection()

    def set_items(self):
        self.items = {item.id: item for item in self.db_manager.session.query(
            Item).filter(Item.source == self.publisher).all()}

    def match_log_info_with_drb_data(self, log_object):
        match_request = re.search(REQUEST_REGEX, log_object)
        match_referrer = re.search(str(self.referrer_url), log_object)

        if not match_request or not match_referrer or "403 AccessDenied" in log_object:
            return None

        match_time = re.search(TIMESTAMP_REGEX, log_object)
        match_file_id = re.search(FILE_ID_REGEX, log_object)
        match_ip = re.search(IP_REGEX, log_object)
        link_group = match_file_id.group(1)

        link_data = self.db_manager.session.query(Link, ITEM_LINKS) \
            .join(ITEM_LINKS) \
            .filter(ITEM_LINKS.c.item_id.in_(self.items.keys())) \
            .filter(Link.media_type == "application/pdf") \
            .filter(Link.url.contains(link_group.strip())) \
            .first()

        if not link_data:
            return None

        _, item_id, _ = link_data

        item = self.items.get(item_id)
        edition = self.db_manager.session.get(Edition, item.edition_id)

        title = edition.title
        publication_year = self.pull_publication_year(edition)

        record = self.db_manager.session.query(Record) \
            .filter(Record.uuid.in_(edition.dcdw_uuids)) \
            .filter(Record.publisher_project_source == item.publisher_project_source) \
            .first()

        book_id = f'{self.referrer_url}edition/{item.edition_id}'
        usage_type = self.determine_usage(record)
        isbns = [identifier.split("|")[0] for identifier in record.identifiers if "isbn" in identifier]
        oclc_numbers = [identifier.split("|")[0] for identifier in record.identifiers if "oclc" in identifier]

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
            interaction_type=InteractionType.DOWNLOAD,
            timestamp=match_time.group(0)
        )
