import calendar
import csv
import pandas
import uuid

from abc import ABC, abstractmethod
from dataclasses import fields, is_dataclass
from datetime import datetime
from typing import Any, List


class Counter5Report(ABC):
    def __init__(self, publisher, reporting_period):
        self.publisher = publisher
        self.created = datetime.today().strftime("%Y-%m-%d")
        self.reporting_period = reporting_period

    @abstractmethod
    def build_report(self, events):
        return

    def generate_report_id(self):
        return uuid.uuid4()
    
    def aggregate_interaction_events(self, events):
        df = pandas.DataFrame([self._format_dataclass_for_df(event) for event in events])
        df.columns = [
            "Book Title",
            "Book ID",
            "Authors",
            "ISBN(s)",
            "OCLC Number(s)",
            "Publication Year",
            "Disciplines",
            "Usage Type",
            "Interaction Type",
            "Timestamp"
        ]
        df["Timestamp"] = df["Timestamp"].apply(self._reformat_timestamp_data)
        df_unique = df.drop_duplicates(subset="Book ID")
        df_grouped_by_id_and_month = df.groupby(["Book ID", pandas.Grouper(freq='M', key='Timestamp')])
        monthly_columns = []

        for key, group in df_grouped_by_id_and_month:
            month, year = key[1].month, key[1].year
            column_name = "{0} {1}".format(calendar.month_name[int(month)], year)
            f"{month}-{year}"

            if column_name not in df_unique.columns:
                monthly_columns.append(column_name)
                df_unique[column_name] = pandas.Series()
            
            df_unique.loc[df_unique["Book ID"] == key[0], column_name] = group["Book ID"].count()

        df_unique.drop(columns=["Timestamp", "Interaction Type"], axis=1, inplace=True)
        df_unique.loc[:, monthly_columns] = df_unique[monthly_columns].fillna(0)
        df_unique.loc[:, "Reporting Period Total"] = df_unique[monthly_columns].sum(axis=1)
        
        return (df_unique.columns.tolist(), df_unique.to_dict(orient="records"))
    
    def aggregate_interaction_events_by_country(self, events):
        df = pandas.DataFrame([self._format_dataclass_for_df(event, include_country=True) for event in events])
        df.columns = [
            "Country",
            "Book Title",
            "Book ID",
            "Authors",
            "ISBN(s)",
            "OCLC Number(s)",
            "Publication Year",
            "Disciplines",
            "Usage Type",
            "Interaction Type",
            "Timestamp"
        ]
        df["Timestamp"] = df["Timestamp"].apply(self._reformat_timestamp_data)
        df_unique = df.drop_duplicates(subset=["Country", "Book ID"])
        df_grouped_by_country_id_and_month = df.groupby(["Country", "Book ID", pandas.Grouper(freq='M', key='Timestamp')])
        monthly_columns = []

        for key, group in df_grouped_by_country_id_and_month:
            country, book_id, date = key
            month, year = date.month, date.year
            column_name = "{0} {1}".format(calendar.month_name[int(month)], year)
            f"{month}-{year}"

            if column_name not in df_unique.columns:
                monthly_columns.append(column_name)
                df_unique[column_name] = pandas.Series()
            
            df_unique.loc[(df_unique["Country"] == country) & (df_unique["Book ID"] == book_id), column_name] = group["Book ID"].count()

        df_unique.drop(columns=["Timestamp", "Interaction Type"], axis=1, inplace=True)
        df_unique.loc[:, monthly_columns] = df_unique[monthly_columns].fillna(0)
        df_unique.loc[:, "Reporting Period Total"] = df_unique[monthly_columns].sum(axis=1)
        
        return (df_unique.columns.tolist(), df_unique.to_dict(orient="records"))
    
    def build_header(self, report_name, report_description):
        return {
            "Report_Name": report_name,
            "Report_ID": self.generate_report_id(),
            "Report_Description": report_description,
            "Publisher_Name": self.publisher,
            "Reporting_Period": self._format_reporting_period_to_string(),
            "Created": self.created,
            "Created_By": "NYPL",
        }
    
    def write_to_csv(self, file_name, header, column_names, data):
        with open(file_name, 'w') as csv_file:
            writer = csv.writer(csv_file, delimiter="|")
            for key, value in header.items():
                writer.writerow([key, value])
            writer.writerow([])
            writer.writerow(column_names)
            for title in data:
                writer.writerow(title.values())
    
    def _format_reporting_period_to_string(self):
        return (self.reporting_period[0].strftime("%Y-%m-%d") + 
                " to " + 
                self.reporting_period[-1].strftime("%Y-%m-%d"))

    def _format_dataclass_for_df(self, dataclass_instance: Any, include_country=False) -> List[Any]:
        if not is_dataclass(dataclass_instance):
            raise ValueError("Provided instance is not a dataclass.")
        
        csv_row = []

        for field in fields(dataclass_instance):
            if field.name == 'country' and not include_country:
                continue

            csv_row.append(getattr(dataclass_instance, field.name))
        
        return csv_row
    
    def _reformat_timestamp_data(self, date):
        string_date = str(date).strip("[]").split(":")[0]
        return pandas.to_datetime(string_date)
