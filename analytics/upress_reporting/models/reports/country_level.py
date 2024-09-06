from models.reports.counter_5_report import Counter5Report


class CountryLevelReport(Counter5Report):
    def __init__(self, *args):
        super().__init__(*args)

    def build_report(self, events):
        print("Building country-level report...")
        
        if len(events) > 0:
            file_name = f"{self.publisher}_country_level_report_{self.created}.csv"
            header = self.build_header(report_name="NYPL DRB Book Usage by Country",
                                       report_description="Usage of your books on NYPL's Digital Research Books by country.")
            columns, final_data = self.aggregate_interaction_events_by_country(events)
            
            self.write_to_csv(file_name=file_name,
                              header=header,
                              column_names=columns,
                              data=final_data)

            print("Country-level report generation complete!")
        else:
            print("No events found in reporting period!")

