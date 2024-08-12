import boto3
import re
import os

from analytics.upress_reporting.models.aggregators.aggregator import Aggregator
from analytics.upress_reporting.models.data.interaction_event import InteractionEvent
from logger import createLog
from managers.db import DBManager

# Regexes needed to parse S3 logs
REQUEST_REGEX = r"REST.GET.OBJECT "
# File ID includes the file name for the pdf object
FILE_ID_REGEX = r"REST\.GET\.OBJECT manifests/(.+)/(.+json\s)"
TIMESTAMP_REGEX = r"\[.+\]"
REFERRER_REGEX = r"https://drb-qa.nypl.org/"

class ViewDataAggregator(Aggregator):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("VIEW_BUCKET", None)
        self.log_path = os.environ.get("VIEW_LOG_PATH", None)

        self.logger = createLog("view_data_aggregator")
        self.setup_db_manager() 
    
    def pull_interaction_events(self) -> list[InteractionEvent]:
        '''
        Returns list of view InteractionEvents in a given reporting period.
        '''
        # TODO: potentially move this into general aggregator?
        view_events = []

        for date in self.date_range:
            folder_name = date.strftime("%Y/%m/%d")
            batch = self.load_batch(self.log_path, self.bucket_name, 
                                    folder_name)
            views_per_day = self.parse_logs_in_batch(batch, self.bucket_name)
            view_events.extend(views_per_day)

        self.db_manager.closeConnection()
        return view_events
