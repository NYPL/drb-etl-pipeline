from datetime import datetime, timedelta, timezone
import os
import requests
import json
import urllib.parse
from typing import Optional

from logger import create_log
from mappings.UofM import UofMMapping
from .source_service import SourceService


logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=UofMichigan%20Press"
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
    ) -> list[UofMMapping]:
        
        array_json_records = self.get_records_json(full_import, start_timestamp, offset, limit)

        array_index = 0
        while array_index != len(array_json_records):
            for dict_index in range(0, len(array_json_records[array_index]['records'])):
                meta_dict = array_json_records[array_index]['records'][dict_index]
                raise Exception
            array_index += 1

    def get_records_json(self, full_import=False, start_timestamp=None, offset=None, limit=None):

        if offset == None:
            limit = 100

        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}

        if not full_import:
            if start_timestamp:
                start_date_time_str = start_date_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                start_date_time_encoded = urllib.parse.quote(start_date_time_str)
                filter_by_formula = f"OR(IS_SAME(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22,%20%22second%22),%20IS_AFTER(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22))"

                response = requests.get(f'{BASE_URL}&filterByFormula={filter_by_formula}&pageSize={limit}', headers=headers)
                response_json = response.json()
                array_json = [response_json]

                while 'offset' in response_json:
                    offset = response_json['offset']
                    response = requests.get(f'{BASE_URL}&filterByFormula={filter_by_formula}&pageSize={limit}&offset={offset}', headers=headers)
                    response_json = response.json()
                    array_json.append(response_json)

                return array_json
            else:
                start_date_time = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
                start_date_time_str = start_date_time.strftime("%Y-%m-%d %H:%M:%S.%f")
                start_date_time_encoded = urllib.parse.quote(start_date_time_str)
                filter_by_formula = f"OR(IS_SAME(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22,%20%22second%22),%20IS_AFTER(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22))"
                
                response = requests.get(f'{BASE_URL}&filterByFormula={filter_by_formula}&pageSize={limit}', headers=headers)
                response_json = response.json()
                array_json = [response_json]

                while 'offset' in response_json:
                    offset = response_json['offset']
                    response = requests.get(f'{BASE_URL}&filterByFormula={filter_by_formula}&pageSize={limit}&offset={offset}', headers=headers)
                    response_json = response.json()
                    array_json.append(response_json)

                return array_json
        else:
            response = requests.get(f'{BASE_URL}&pageSize={limit}', headers=headers)
            response_json = response.json()
            array_json = [response_json]

            while 'offset' in response_json:
                offset = response_json['offset']
                response = requests.get(f'{BASE_URL}&pageSize={limit}&offset={offset}', headers=headers)
                response_json = response.json()
                array_json.append(response_json)

            return array_json
        
