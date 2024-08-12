from logger import createLog
from models.reports.counter_5_report import Counter5Report


class ViewsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
        self.logger = createLog("views_report")
    
    def build_report(self):
        return
    
    def build_header(self):
        return {
            "Report_Name": "NYPL DRB Book Usage by Title / Views",
            "Report_ID": self.generate_report_id(),
            "Report_Description": "Views of your books from NYPL's Digital Research Books by title.",
            "Publisher_Name": self.publisher,
            "Reporting_Period": self.reporting_period,
            "Created": self.created,
            "Created_By": self.created_by,
        }
