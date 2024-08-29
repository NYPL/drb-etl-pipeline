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
    def __init__(self, reporting_period):
        self.publishers = os.environ.get("PUBLISHERS").split(",")
        
        if reporting_period is not None:
            self.reporting_period = reporting_period
        else:
            self.reporting_period = (f"{datetime.now().year}-01-01 to {datetime.now().year}-01-31")

    def create_reports(self):
        print("Generating Counter 5 reports...")

        pandas_reporting_period = self._parse_reporting_period(self.reporting_period)

        for publisher in self.publishers:
            try:
                view_data_poller = ViewDataPoller(publisher, pandas_reporting_period)
                download_data_poller = DownloadDataPoller(publisher, pandas_reporting_period)

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

        print("Done building Counter 5 reports!")

    def _parse_reporting_period(self, reporting_period, freq="D"):
        date_pattern = "20[0-9][0-9](.|-|)(\\d\\d)(.|-|)(\\d\\d)"
        fiscal_quarter_pattern = "20[0-9][0-9]Q[1-4]"

        if re.search(("^" + date_pattern + "\\sto\\s" + date_pattern), reporting_period):
            start, end = reporting_period.split(" to ")
            return pandas.date_range(start=start, end=end, freq=freq)
        
        if re.search(fiscal_quarter_pattern, reporting_period):
            period = pandas.Period(reporting_period, freq="Q-JUN")
            return pandas.date_range(start=period.start_time,
                                     end=period.end_time, 
                                     freq=freq)
