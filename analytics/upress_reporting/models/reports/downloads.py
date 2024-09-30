from models.reports.counter_5_report import Counter5Report


class DownloadsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events):
        print("Building downloads report...")

        if len(events) > 0:
            file_name = f"{self.publisher}_downloads_report_{self.created}.csv"
            header = self.build_header(report_name="NYPL DRB Book Usage by Title / Downloads",
                                       report_description="Downloads of your books from NYPL's Digital Research Books by title.")
            columns, final_data = self.aggregate_interaction_events(events)
            
            self.write_to_csv(file_name=file_name,
                              header=header,
                              column_names=columns,
                              data=final_data)
            
            print("Downloads report generation complete!")
        else:
            print("No download events found in reporting period!")
