from analytics.upress_reporting.models.reports.counter_5_report import Counter5Report


class CountryLevelReport(Counter5Report):
    def __init__(self, publisher):
        super().__init__(publisher)
