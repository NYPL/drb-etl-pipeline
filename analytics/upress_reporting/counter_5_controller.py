import argparse
import os
import pandas

from datetime import datetime

from helpers import aggregate_logs
from managers.db import DBManager
from model.postgres.edition import Edition
from model.postgres.item import Item
from models.pollers.download_data_poller import DownloadDataPoller
from models.pollers.view_data_poller import ViewDataPoller
from model.postgres.record import Record
from models.reports.country_level import CountryLevelReport
from models.reports.downloads import DownloadsReport
from models.reports.total_usage import TotalUsageReport
from models.reports.views import ViewsReport
from sqlalchemy import func
from typing import List

VIEW_FILE_ID_REGEX = r"REST.GET.OBJECT manifests/(.*?json)\s"
DOWNLOAD_FILE_ID_REGEX = r"REST.GET.OBJECT (.+pdf\s)"


class Counter5Controller:
    def __init__(self, args):
        self.publishers = os.environ.get("PUBLISHERS").split(",")

        parsed_args = self._parse_args(args)
        if parsed_args is not None:
            self.reporting_period = self._parse_reporting_period(parsed_args)
        else:
            self.reporting_period = (
                f"{datetime.now().year}-01-01 to {datetime.now().year}-01-31")

        self.setup_db_manager()

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

    def pull_aggregated_logs(self):
        referrer_url = os.environ.get("REFERRER_URL", None)

        aggregate_logs.aggregate_logs_in_period(date_range=self.reporting_period,
                                                s3_bucket=os.environ.get(
                                                    "VIEW_BUCKET", None),
                                                s3_path=os.environ.get(
                                                    "VIEW_LOG_PATH", None),
                                                regex=VIEW_FILE_ID_REGEX,
                                                referrer_url=referrer_url)

        aggregate_logs.aggregate_logs_in_period(date_range=self.reporting_period,
                                                s3_bucket=os.environ.get(
                                                    "DOWNLOAD_BUCKET", None),
                                                s3_path=os.environ.get(
                                                    "DOWNLOAD_LOG_PATH", None),
                                                regex=DOWNLOAD_FILE_ID_REGEX,
                                                referrer_url=referrer_url)

    def pull_publisher_data(self, publisher):
        print("Printing publisher data...", datetime.now())
        # purpose of this method -> minimize db calls
        records = self.db_manager.session.query(Record) \
            .filter((Record.source == publisher)).all()
        editions = self.db_manager.session.query(Edition).all()

        relevant_data = self.db_manager.session.query(Record.has_part, Record.identifiers, 
                                                      Record.uuid, Record.authors, Record.subjects, 
                                                      Edition.id, Edition.title, Edition.dates) \
            .join(Edition, func.array_to_string(Edition.dcdw_uuids, ',').ilike(f'%{Record.uuid}%')) \
            .filter(Record.publisher_project_source == publisher) \
            .all()

        #     select(Record.has_part, Record.identifiers, Record.uuid, Record.authors,
        #            Record.subjects, Edition.id, Edition.title, Edition.dates)
        #     .filter(Edition.dcdw_uuids.contains(f"{{{Record.uuid}}}"))
        # ).all()

        # .filter(Record.source == publisher)

        print("Hmm ", relevant_data)
        exit()
        return (records, editions)

    def build_reporting_model(self, records: List[Record], editions: List[Edition]):
        print("here", datetime.now())
        print("|".join(editions[0].dcdw_uuids))
        editions_uuids = {"|".join(edition.dcdw_uuids): edition for edition in editions}
        records_dict = {}

        for record in records:
            related_editions = [
                value for key, value in editions_uuids.items() if record.uuid in key.lower()]
            records_dict["|".join(record.has_part)] = {
                "record_data": record, "associated_edition": related_editions[0]}

        return records_dict

    def create_reports(self):
        print("Generating Counter 5 reports...")
        # TODO: aggregate log files -> * one for views and one for downloads (this is agnostic of publisher)

        # TODO: get all records and editions from publisher backlists stored in config

        # TODO: map records/editions data to reporting model

        # TODO: create a map of record_id to record
        # TODO: create a map of each relevant part in record.has_part to record_id

        # self.pull_aggregated_logs()

        for publisher in self.publishers:
            try:
                # TODO: pass in prepped data
                records, editions = self.pull_publisher_data(publisher)
                records_dict = self.build_reporting_model(records, editions)
                print("Records dict ", records_dict)

                view_data_poller = ViewDataPoller(
                    publisher, self.reporting_period)
                download_data_poller = DownloadDataPoller(
                    publisher, self.reporting_period)

                downloads_report = DownloadsReport(
                    publisher, self.reporting_period)
                downloads_report.build_report(download_data_poller.events)

                views_report = ViewsReport(publisher, self.reporting_period)
                views_report.build_report(view_data_poller.events)

                country_level_report = CountryLevelReport(
                    publisher, self.reporting_period)
                country_level_report.build_report(
                    view_data_poller.events + download_data_poller.events)

                total_usage_report = TotalUsageReport(
                    publisher, self.reporting_period)
                total_usage_report.build_report(
                    view_data_poller.events + download_data_poller.events)
            except Exception as e:
                print("Terminating process. Exception encountered: ", e)
                raise e

        self.db_manager.closeConnection()
        print("Done building Counter 5 reports! ", datetime.now())

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(prog="Counter 5 Report Generator")

        parser.add_argument("--start", "-s",
                            help="starting date in the format yyyy-mm-dd")
        parser.add_argument("-e", "--end",
                            help="end date in the format yyyy-mm-dd")
        parser.add_argument("-y", "--year",
                            help="fiscal year, ex. 2024")
        parser.add_argument("-q", "--quarter",
                            help="fiscal quarter, ex. Q1")

        return parser.parse_args(args)

    def _parse_reporting_period(self, parsed_args, freq="D"):
        if parsed_args.start and parsed_args.end:
            start, end = parsed_args.start, parsed_args.end
            return pandas.date_range(start=start, end=end, freq=freq)

        if parsed_args.year and parsed_args.quarter:
            period = pandas.Period(parsed_args.year + parsed_args.quarter,
                                   freq="Q-JUN")
            return pandas.date_range(start=period.start_time,
                                     end=period.end_time,
                                     freq=freq)
