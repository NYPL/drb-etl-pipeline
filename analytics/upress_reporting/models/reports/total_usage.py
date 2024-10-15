from models.reports.counter_5_report import Counter5Report


class TotalUsageReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events, reporting_data):
        print("Building total usage report...")

        if len(events) > 0:
            file_name = f"{self.publisher}_total_usage_{self.created}.csv"
            header = self.build_header(report_name="NYPL DRB Total Item Requests by Title",
                                       report_description="Usage of your books on NYPL's Digital Research Books.")
            columns, final_data = self.aggregate_interaction_events(events, reporting_data)
            
            self.write_to_csv(file_name=file_name,
                              header=header,
                              column_names=columns,
                              data=final_data)

            print("Total usage report generation complete!")
        else:
            print("No events found in reporting period!")
