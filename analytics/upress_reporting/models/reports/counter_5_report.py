import calendar
import pandas
import re
import uuid

from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any, List


class Counter5Report(ABC):
    def __init__(self, publisher, reporting_period=None):
        self.publisher = publisher
        self.created = datetime.today().strftime("%Y-%m-%d")
        self.created_by = "NYPL"
        if reporting_period is not None:
            self.reporting_period = reporting_period
        else:
            # set reporting period to first month of current year
            self.reporting_period = (
                f"{datetime.now().year}-01-01 to {datetime.now().year}-01-31"
            )
        self.pandas_date_range = self._parse_reporting_period(
            self.reporting_period)

    @abstractmethod
    def build_header(self) -> dict:
        return

    @abstractmethod
    def build_report(self):
        return

    def generate_report_id(self):
        return uuid.uuid4()
    
    def aggregate_interaction_events(self, events):
        '''
        Builds counts for each title in each month in the reporting period.
        '''
        # TODO: break up this large method
        df = pandas.DataFrame(
            [self._format_dataclass_for_csv(event) for event in events])
        df.columns = ["Book Title",
           "Book ID",
           "Authors",
           "ISBN(s)",
           "Copyright Year",
           "Publication Year",
           "Disciplines",
           "Usage Type",
           "Interaction Type",
           "Timestamp"]
        # convert column from str type to Timestamp type for easier grouping
        df["Timestamp"] = df["Timestamp"].apply(
            self._reformat_timestamp_data)

        '''
        Remove all duplicate titles for CSV report. We will populate df_unique's 
        monthly columns based on df_grouped_by_id_and_month
        '''
        df_unique = df.drop_duplicates(subset="Book ID")
        df_grouped_by_id_and_month = df.groupby(
            ["Book ID", pandas.Grouper(freq='M', key='Timestamp')])
        monthly_columns = []

        for keys, group in df_grouped_by_id_and_month:
            # example key values ->  Keys: ('756467457', Timestamp('2024-04-30 00:00:00'))
            month, year = keys[1].month, keys[1].year
            column_name = "{0} {1}".format(calendar.month_name[int(month)], 
                                           year)
            f"{month}-{year}"
            if column_name not in df_unique.columns:
                monthly_columns.append(column_name)
                # create a new column for each month in the reporting period
                df_unique[column_name] = pandas.Series()
            # populate counts for a given title per month
            df_unique.loc[df_unique["Book ID"] == keys[0],
                          column_name] = group["Book ID"].count()

        # delete now-unnecessary data
        df_unique.drop(columns=["Timestamp", "Interaction Type"], 
                       axis=1,
                       inplace=True)
        # set null values to 0
        df_unique.loc[:, monthly_columns] = df_unique[monthly_columns].fillna(0)
        # set reporting period total for each title
        df_unique.loc[:, "Reporting Period Total"] = df_unique[monthly_columns].sum(
            axis=1)
        
        # return tuple of new columns for CSV labeling
        return (df_unique.columns.tolist(), df_unique.to_dict(orient="records"))
    
    def _parse_reporting_period(self, reporting_period, freq='D'):
        """
        Helper method to transform user input into date_range object.
        Input: String with date range in Y-m-d format (ex. "2024-01-01 to 2024-12-31")
        Output: Pandas date_range
        """
        date_pattern = "20[0-9][0-9](.|-|)(\\d\\d)(.|-|)(\\d\\d)"

        if re.search(
            ("^" + date_pattern + "\\sto\\s" + date_pattern), reporting_period
        ):
            start, end = reporting_period.split(" to ")
            return pandas.date_range(start=start, end=end, freq=freq)
    
    def _format_dataclass_for_csv(self, dataclass_instance: Any) -> List[Any]:
        if not is_dataclass(dataclass_instance):
            raise ValueError("Provided instance is not a dataclass.")
        
        csv_row = []
        for field in fields(dataclass_instance):
            csv_row.append(getattr(dataclass_instance, field.name))
        return csv_row
    
    def _reformat_timestamp_data(self, date):
        '''
        Converts strings to Pandas Timestamp objects.
        '''
        string_date = str(date).strip("[]").split(":")[0]
        return pandas.to_datetime(string_date)

