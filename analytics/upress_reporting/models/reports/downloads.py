import csv
import pandas

from logger import createLog
from models.aggregators.download_data_aggregator import DownloadDataAggregator
from models.reports.counter_5_report import Counter5Report


class DownloadsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
        self.download_request_parser = DownloadDataAggregator(self.publisher, self.pandas_date_range)

    def build_report(self):
        # TODO: building report is slow, create a follow up story?
        print("Building downloads report...")

        header = self.build_header()
        download_events = self.download_request_parser.events

        if len(download_events) > 0:
            columns, final_data = self.aggregate_interaction_events(
                download_events)
            csv_file_name = f"{self.publisher}_downloads_report_{self.created}.csv"
            
            with open(csv_file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter="|")
                for key, value in header.items():
                    writer.writerow([key, value])
                writer.writerow([])
                writer.writerow(columns)
                for title in final_data:
                    writer.writerow(title.values())

            print("Downloads report generation complete!")
        else:
            print("No download events found in reporting period!")

    def build_header(self):
        return {
            "Report_Name": "NYPL DRB Book Usage by Title / Downloads",
            "Report_ID": self.generate_report_id(),
            "Report_Description": "Downloads of your books from NYPL's Digital Research Books by title.",
            "Publisher_Name": self.publisher,
            "Reporting_Period": self.reporting_period,
            "Created": self.created,
            "Created_By": self.created_by,
        }
