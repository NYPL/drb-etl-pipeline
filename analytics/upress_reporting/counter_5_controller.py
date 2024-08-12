import os

from datetime import datetime
from models.reports.downloads import DownloadsReport
from models.reports.views import ViewsReport
from nypl_py_utils.functions.log_helper import create_log


class Counter5Controller:
    """Class for orchestrating various Counter 5 reports"""

    def __init__(self, reporting_period):
        self.logger = create_log("counter_5_controller")
        self.publishers = os.environ.get("PUBLISHERS").split(",")
        if reporting_period is not None:
            self.reporting_period = reporting_period
        else:
            # set reporting period to first month of current year
            self.reporting_period = (
                f"{datetime.now().year}-01-01 to {datetime.now().year}-01-31"
            )

    def create_reports(self):
        self.logger.info("Generating Counter 5 reports...")

        for publisher in self.publishers:
            reports = self._setup_reports(publisher, self.reporting_period)
            try:
                for report in reports:
                    report.build_report()
            except Exception as e:
                self.logger.error(
                    "Terminating process. Exception encountered: ", e)
                raise e

        self.logger.info("Done building Counter 5 reports!")

    def _setup_reports(self, publisher, reporting_period):
        return [
            DownloadsReport(publisher, reporting_period)
            # ViewsReport(publisher, reporting_period)
        ]
