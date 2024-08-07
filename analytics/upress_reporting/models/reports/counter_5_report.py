import pandas
import re
import uuid

from abc import ABC, abstractmethod
from datetime import datetime


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

    @abstractmethod
    def build_header(self) -> dict:
        return

    @abstractmethod
    def build_report(self):
        return

    @abstractmethod
    def aggregate_interaction_events(self, events) -> pandas.DataFrame:
        return

    def generate_report_id(self):
        return uuid.uuid4()

    def parse_reporting_period(self, reporting_period, freq='D'):
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
