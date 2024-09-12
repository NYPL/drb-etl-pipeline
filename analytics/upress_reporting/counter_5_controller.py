import argparse
from ast import parse
import os
import pandas
import re

from datetime import datetime
from models.pollers.download_data_poller import DownloadDataPoller
from models.pollers.view_data_poller import ViewDataPoller
from models.reports.country_level import CountryLevelReport
from models.reports.downloads import DownloadsReport
from models.reports.total_usage import TotalUsageReport
from models.reports.views import ViewsReport


class Counter5Controller:
    def __init__(self, args):
        self.publishers = os.environ.get("PUBLISHERS").split(",")
        parsed_args = self._parse_args(args)
        if parsed_args is not None:
            self.reporting_period = self._parse_reporting_period(parsed_args)
        else:
            self.reporting_period = (f"{datetime.now().year}-01-01 to {datetime.now().year}-01-31")

    def create_reports(self):
        print("Generating Counter 5 reports...", datetime.now())

        for publisher in self.publishers:
            try:
                view_data_poller = ViewDataPoller(publisher, self.reporting_period)
                download_data_poller = DownloadDataPoller(publisher, self.reporting_period)

                downloads_report = DownloadsReport(publisher, self.reporting_period)
                downloads_report.build_report(download_data_poller.events)

                views_report = ViewsReport(publisher, self.reporting_period)
                views_report.build_report(view_data_poller.events)

                country_level_report = CountryLevelReport(publisher, self.reporting_period)
                country_level_report.build_report(view_data_poller.events + download_data_poller.events)

                total_usage_report = TotalUsageReport(publisher, self.reporting_period)
                total_usage_report.build_report(view_data_poller.events + download_data_poller.events)
            except Exception as e:
                print("Terminating process. Exception encountered: ", e)
                raise e

        print("Done building Counter 5 reports! ", datetime.now())

    def _parse_args(self, args):
        parser = argparse.ArgumentParser(prog="Counter 5 Report Generator")
        
        parser.add_argument( "--start", "-s", 
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
