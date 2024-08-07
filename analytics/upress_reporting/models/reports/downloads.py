import csv
import pandas

from helpers.download_data_aggregator import DownloadDataAggregator
from models.reports.counter_5_report import Counter5Report
from logger import createLog

COLUMNS = ["Book Title",
           "Book ID",
           "Authors",
           "ISBN(s)",
           "eISBN(s)",
           "Copyright Year",
           "Disciplines",
           "Usage Type",
           "Interaction Type"
           "Timestamp"]


class DownloadsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
        pandas_date_range = self.parse_reporting_period(
            self.reporting_period)
        self.download_request_parser = DownloadDataAggregator(
            self.publisher, pandas_date_range)
        self.logger = createLog("downloads_report")

    def build_report(self):
        # TODO: building report is slow, create a follow up story?
        self.logger.info("Building downloads report...")

        header = self.build_header()
        download_events = self.download_request_parser.pull_download_events()
        df = self.aggregate_interaction_events(download_events)

        csv_file_name = f"{self.publisher}_downloads_report_{self.created}.csv"
        with open(csv_file_name, 'w') as csv_file:
            writer = csv.writer(csv_file)
            for key, value in header.items():
                writer.writerow([key, value])
            writer.writerow([])
            # following code is temp until we can integrate DRB data
            writer.writerow(COLUMNS)
            for download_event in download_events:
                writer.writerow(download_event.format_for_csv())

        self.logger.info("Downloads report generation complete!")

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

    def aggregate_interaction_events(self, events):
        '''
        Builds counts for each title in each month in the reporting period.
        '''
        df = pandas.DataFrame(
            [self.format_dataclass_for_csv(event) for event in events])
        df.columns = COLUMNS
        # convert timestamp column from str type to Timestamp type for easier grouping
        df["Timestamp"] = df["Timestamp"].apply(
            self._reformat_timestamp_data)
        print("Dataframe ", df)
        df_grouped_by_title_and_month = df.groupby(
            ["Book Title", pandas.Grouper(freq='M', key='Timestamp')])
        print("there ", df_grouped_by_title_and_month)

        '''
        Remove all duplicate titles for CSV report. We will populate df_unique's 
        monthly columns based on df_grouped_by_title_and_month
        '''
        df_unique = df.drop_duplicates(subset="Book ID")
        column_names = []

        for keys, group in df_grouped_by_title_and_month:
            # example key values ->  Keys: ('756467457', Timestamp('2024-04-30 00:00:00'))
            month, year = keys[1].month, keys[1].year
            column_name = f"{month}/{year}"
            column_names.append(column_name)
            if column_name not in df_unique:
                # create a new column for each month in the reporting period
                df_unique[f"{month}/{year}"] = pandas.Series()
            # populate counts for a given title per month
            df_unique.loc[df_unique["Book ID"] == keys[0],
                          column_name] = group["Book ID"].count()

        # set null values to 0
        df_unique[column_names] = df_unique[column_names].fillna(
            value=0, axis=1)
        # set reporting period total for each title
        df_unique["Reporting Period Total"] = df_unique[column_names].sum(
            axis=1)
        df_unique.drop(columns=["Timestamp", "Interaction Type"], axis=1)
        print("Unique df ", df_unique)
        return df_unique

    def _reformat_timestamp_data(self, date):
        '''
        Converts strings to Pandas Timestamp objects.
        '''
        string_date = str(date).strip("[]").split(":")[0]
        return pandas.to_datetime(string_date)
