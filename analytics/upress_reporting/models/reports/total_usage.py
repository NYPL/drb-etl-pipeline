from models.reports.counter_5_report import Counter5Report


class TotalUsageReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events):
        print("Building total usage report...")

        header = self.build_header()

        if len(events) > 0:
            columns, final_data = self.aggregate_interaction_events(events)
            file_name = f"{self.publisher}_total_usage_{self.created}.csv"
            self.write_to_csv(file_name=file_name,
                              header=header,
                              column_names=columns,
                              data=final_data)

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
