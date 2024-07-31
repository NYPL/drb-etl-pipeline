from analytics.upress_reporting.models.reports.counter_5_report import Counter5Report


class ViewsReport(Counter5Report):
    def __init__(self, publisher):
        super().__init__(publisher)
