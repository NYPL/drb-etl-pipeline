from models.reports.counter_5_report import Counter5Report


class TotalUsageReport(Counter5Report):
    def __init__(self, publisher):
        super().__init__(publisher)
