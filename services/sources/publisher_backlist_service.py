from datetime import datetime, timedelta, timezone
import os
import requests
import json
from typing import Optional

from logger import create_log
from mappings.UofM import UofMMapping
from .source_service import SourceService


logger = create_log(__name__)


class PublisherBacklistService(SourceService):
    def __init__(self):
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)

        pass

    def get_records(
        self,
        full_import: bool=False, # get all records from Airtable
        start_timestamp: datetime=None,
        offset: Optional[int]=None, # start at specific position in paginated results 
        limit: Optional[int]=None
    ) -> list[UofMMapping]:
        
        json_data = self.get_publisher_backlist_records(full_import, start_timestamp, offset, limit)

        array_index = 0
        while array_index != len(json_data):
            for dict_index in range(0, len(json_data['records'])):
                metaDict = json_data['records'][dict_index]
                raise Exception
            array_index += 1

    def get_publisher_backlist_records(self, full_import=False, start_timestamp=None, offset=None, limit=None):

        if offset == None:
            limit = 100

        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}

        if not full_import:
            if start_timestamp:
                response = requests.get(f'https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&pageSize={limit}', headers=headers)
                return response.json()
            else:
                start_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
                response = requests.get(f'https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&pageSize={limit}', headers=headers)
                return response.json
        else:
            response = requests.get(f'https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press', headers=headers)
            response_json = response.json()
            array_json = [response_json]
            while 'offset' in response_json:
                offset = response_json['offset']
                response = requests.get(f'https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press&pageSize={limit}&offset={offset}', headers=headers)
                response_json = response.json()
                array_json.append(response_json)

            return array_json


