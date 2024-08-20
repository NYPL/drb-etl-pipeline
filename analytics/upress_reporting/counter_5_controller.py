import os

from datetime import datetime
from models.reports.downloads import DownloadsReport
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

        for publisher in self.publishers:
            reports = self._setup_reports(publisher, self.reporting_period)
            
            try:
                for report in reports:
                    report.build_report()
            except Exception as e:
                print("Terminating process. Exception encountered: ", e)
                raise e

        print("Done building Counter 5 reports!")

    def _setup_reports(self, publisher, reporting_period):
        return [
            DownloadsReport(publisher, reporting_period),
            ViewsReport(publisher, reporting_period),
        ]
