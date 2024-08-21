import csv

from models.reports.counter_5_report import Counter5Report


class TotalUsageReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events):
        print("Building total usage report...")

        header = self.build_header()

        if len(events) > 0:
            columns, final_data = self.aggregate_interaction_events(events)
            csv_file_name = f"{self.publisher}_total_usage_{self.created}.csv"
            
            with open(csv_file_name, 'w') as csv_file:
                writer = csv.writer(csv_file, delimiter="|")
                for key, value in header.items():
                    writer.writerow([key, value])
                writer.writerow([])
                writer.writerow(columns)
                for title in final_data:
                    writer.writerow(title.values())

            print("Total usage report generation complete!")
        else:
            print("No events found in reporting period!")

    def build_header(self):
        return {
            "Report_Name": "NYPL DRB Book Total Usage by Title",
            "Report_ID": self.generate_report_id(),
            "Report_Description": "Usage of your books on NYPL's Digital Research Books.",
            "Publisher_Name": self.publisher,
            "Reporting_Period": self.reporting_period,
            "Created": self.created,
            "Created_By": self.created_by,
        }
