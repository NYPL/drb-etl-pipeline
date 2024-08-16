from models.reports.counter_5_report import Counter5Report


class CountryLevelReport(Counter5Report):
    def __init__(self, publisher):
        super().__init__(publisher)
    
    def build_header(self):
        return {
            "Report_Name": "NYPL DRB Book Usage by Country",
            "Report_ID": self.generate_report_id(),
            "Report_Description": "Usage of your books on NYPL's Digital Research Books by country.",
            "Publisher_Name": self.publisher,
            "Reporting_Period": self.reporting_period,
            "Created": self.created,
            "Created_By": self.created_by
        }