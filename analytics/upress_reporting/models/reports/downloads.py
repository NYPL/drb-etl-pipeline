import csv

from analytics.upress_reporting.helpers.download_data_aggregator import (
    DownloadDataAggregator,
)
from analytics.upress_reporting.models.reports.counter_5_report import Counter5Report

ADDITIONAL_HEADERS = ["Book Title",
                      "Book ID",
                      "Authors",
                      "ISBN",
                      "eISBN",
                      "Copyright Year",
                      "Disciplines",
                      "Usage Type",
                      "Reporting Period Total"]


class DownloadsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
        pandas_date_range = self.parse_reporting_period(self.reporting_period)
        self.download_request_parser = DownloadDataAggregator(
            self.publisher, pandas_date_range)

    def build_header(self):
        # TODO: what do we term this set of headers?
        return {
            "Report_Name": "NYPL DRB Book Usage by Title / Downloads",
            "Report_ID": self.generate_report_id(),
            "Report_Description": "Downloads of your books from NYPL's Digital Research Books by title.",
            "Publisher_Name": self.publisher,
            "Reporting_Period": self.reporting_period,
            "Created": self.created,
            "Created_By": self.created_by,
        }

    def build_report(self):
        download_events = self.download_request_parser.pull_download_events()
        header = self.build_header()
        with open('counter_5_downloads_report.csv', 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in header.items():
                writer.writerow([key, value])
            writer.writerow("\n")
            writer.writerow(["Title", "Timestamp", "Edition_ID"])
            for download_event in download_events:
                writer.writerow(
                    [download_event.title, download_event.timestamp, download_event.edition_id])
