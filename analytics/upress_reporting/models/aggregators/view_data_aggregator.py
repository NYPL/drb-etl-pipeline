import boto3
import os

from analytics.upress_reporting.models.aggregators.aggregator import Aggregator
from analytics.upress_reporting.models.data.interaction_event import InteractionEvent
from logger import createLog
from managers.db import DBManager

class ViewDataAggregator(Aggregator):
    def __init__(self, *args):
        super().__init__(*args)
        self.bucket_name = os.environ.get("VIEW_BUCKET", None)
        self.log_path = os.environ.get("VIEW_LOG_PATH", None)

        self.logger = createLog("view_data_aggregator")
        self.setup_db_manager() 
    
    def pull_interaction_events(self) -> list[InteractionEvent]:
        return super().pull_interaction_events()
    
    def parse_logs(self, batch):
        '''
        The edition title, identifier, and timestamp are parsed out of the
        S3 server access log files for UMP download requests.
        '''
        return []
    
class ViewParsingError(Exception):
    def __init__(self, message=None):
        self.message = message