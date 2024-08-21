import csv

from models.reports.counter_5_report import Counter5Report


class ViewsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events):
        # TODO: move to general counter 5 class?
        print("Building views report...")

        header = self.build_header()
        
        if len(events) > 0:
            columns, final_data = self.aggregate_interaction_events(events)
            csv_file_name = f"{self.publisher}_views_report_{self.created}.csv"

            with open(csv_file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter="|")
                for key, value in header.items():
                    writer.writerow([key, value])
                writer.writerow([])
                writer.writerow(columns)
                for title in final_data:
                    writer.writerow(title.values())

            print("Views report generation complete!")
        else:
            print("No view events found in reporting period!")

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
