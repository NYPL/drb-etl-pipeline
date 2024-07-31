from nypl_py_utils.functions.log_helper import create_log
from analytics.upress_reporting.models.reports.downloads import DownloadsReport


class Counter5Controller:
    """Class for orchestrating various Counter 5 reports"""
    def __init__(self, reporting_period):
        self.logger = create_log("counter_5_controller")
        self.publishers = []
        self.reporting_period = reporting_period

    def _setup_reports(self, publisher, date_range):
        return [
            DownloadsReport(publisher, date_range)
        ]

    def pull_reports(self):
        self.logger.info("Pulling Counter 5 reports...")
        for publisher in self.publishers:
            return True
