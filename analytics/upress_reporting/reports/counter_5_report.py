import pandas
import re
import uuid

from abc import ABC, abstractmethod
from datetime import datetime


class Counter5Report(ABC):
    def __init__(self, publisher, reporting_period):
        self.publisher = publisher
        self.created = datetime.today().strftime("%Y-%m-%d")
        self.created_by = "NYPL"
        self.reporting_period = reporting_period
    
    @abstractmethod
    def build_header(self) -> dict:
        return

    @abstractmethod
    def build_report(self):
        return
    
    def generate_report_id(self):
        return uuid.uuid4()
    
    def parse_reporting_period(self, reporting_period):
        '''
        Input: String with date range in Y-m-d format (ex. "2024-01-01 to 2024-12-31")
        Output: Pandas date_range object. Default = Date range for Jan of current year
        '''
        date_pattern = "20[0-9][0-9](.|-|)(\\d\\d)(.|-|)(\\d\\d)"
        
        if (re.search(
                ("^" + date_pattern + "\\sto\\s" + date_pattern),
                reporting_period)):
            start, end = reporting_period.split(" to ")
            return pandas.date_range(start=start, end=end)
        
        # otherwise, return reports for first month of the year
        # TODO: determine default reporting period
        current_year = datetime.now().year
        return pandas.date_range(
            f"{current_year}-01-01", f"{current_year}-01-31")
