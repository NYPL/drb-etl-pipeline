from datetime import datetime, timedelta, timezone
import os
import requests
import json
import urllib.parse
from typing import Optional, Dict

from logger import create_log
from mappings.UofM import UofMMapping
from .source_service import SourceService

logger = create_log(__name__)

BASE_URL = "https://api.airtable.com/v0/appBoLf4lMofecGPU/Publisher%20Backlists%20%26%20Collections%20%F0%9F%93%96?view=All%20Lists"

class PublisherBacklistService(SourceService):
    def __init__(self):
        self.airtable_auth_token = os.environ.get('AIRTABLE_KEY', None)

    def get_records(
        self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[UofMMapping]:
        array_json_records = self.get_records_json(full_import, start_timestamp, offset, limit)

        for json_dict in array_json_records:
            for records_value in json_dict['records']:
                try:
                    record_metadata_dict = records_value
                    record = UofMMapping(record_metadata_dict)
                    record.applyMapping()
                except Exception:
                    logger.exception(f'Failed to process Publisher Backlist record')
        return array_json_records

    def get_records_json(self,
        full_import: bool=False, 
        start_timestamp: datetime=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[dict]:
        if offset == None:
            limit = 100

        if not full_import:
            if start_timestamp:
                filter_by_formula = self.build_filter_by_formula_parameter(start_timestamp)

                array_json_records = self.get_records_array(limit, filter_by_formula)

                return array_json_records

            else:
                filter_by_formula = self.build_filter_by_formula_parameter(start_timestamp)

                array_json_records = self.get_records_array(limit, filter_by_formula)

                return array_json_records  
                
        array_json_records = self.get_records_array(limit, filter_by_formula=None)
        
        return array_json_records
        
    def build_filter_by_formula_parameter(self, start_timestamp: datetime=None) -> str:
        if not start_timestamp:
            start_timestamp = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)

        start_date_time_str = start_timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")
        start_date_time_encoded = urllib.parse.quote(start_date_time_str)
        is_same_date_time_filter = f"IS_SAME(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22"
        is_after_date_time_filter = f"%20IS_AFTER(%7BLast%20Modified%7D,%20%22{start_date_time_encoded}%22"
        filter_by_formula = f"OR({is_same_date_time_filter}),{is_after_date_time_filter}))"

        return filter_by_formula
        
    def get_records_array(self,
        limit: Optional[int]=None, 
        filter_by_formula: str=None,
    ) -> list[dict]:
        url = f'{BASE_URL}&pageSize={limit}'
        headers = {"Authorization": f"Bearer {self.airtable_auth_token}"}

        if filter_by_formula:
            url += f'&filterByFormula{filter_by_formula}'

        pub_backlist_records_response = requests.get(url, headers=headers)
        pub_backlist_records_response_json = pub_backlist_records_response.json()
        array_json = [pub_backlist_records_response_json]
        
        while 'offset' in pub_backlist_records_response_json:
            next_page_url = url + f"&offset={pub_backlist_records_response_json['offset']}"
            pub_backlist_records_response = requests.get(next_page_url, headers=headers)
            pub_backlist_records_response_json = pub_backlist_records_response.json()
            array_json.append(pub_backlist_records_response_json)

        return array_json
