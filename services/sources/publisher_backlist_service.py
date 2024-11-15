from datetime import datetime, timedelta, timezone
import os
import requests
from typing import Optional

from logger import create_log
from mappings.record_mapping import RecordMapping
from .source_service import SourceService


logger = create_log(__name__)


class PublisherBacklistService(SourceService):
    def __init__(self):
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)

        pass

    def get_records(
        self,
        full_import: bool=False,
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[RecordMapping]:
        pass

    def get_publisher_backlist_records(self):
        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}

        response = requests.get('https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&maxRecords=3', headers=headers)

        return response.json()
