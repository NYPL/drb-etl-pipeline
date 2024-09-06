from models.reports.counter_5_report import Counter5Report


class ViewsReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)
    
    def build_report(self, events):
        # TODO: move to general counter 5 class?
        print("Building views report...")

        if len(events) > 0:
            file_name = f"{self.publisher}_views_report_{self.created}.csv"
            header = self.build_header(report_name="NYPL DRB Book Usage by Title / Views",
                                       report_description="Views of your books from NYPL's Digital Research Books by title.")
            columns, final_data = self.aggregate_interaction_events(events)
            
            self.write_to_csv(file_name=file_name, 
                              header=header, 
                              column_names=columns, 
                              data=final_data)
            
            print("Views report generation complete!") 
        else:
            print("No view events found in reporting period!")
