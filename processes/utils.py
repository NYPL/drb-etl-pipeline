from datetime import datetime, timedelta, timezone
from typing import Optional
import re

def get_start_datetime(process_type: Optional[str]=None, ingest_period: Optional[str]=None) -> Optional[str]:
    if ingest_period is not None:
        return datetime.strptime(ingest_period, '%Y-%m-%dT%H:%M:%S')

    if process_type == 'daily':
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
    
    if process_type == 'weekly':
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    
    return None

def clean_formatted_string(formatted_string):
    # Remove extra spaces from combining multiple subfields
    str_no_dupe_spaces = re.sub(r'\s{2,}', ' ', formatted_string)

    # Remove spaces at ends of strings, including extraneous punctuation
    # The negative lookbehind preserves punctuation with initialisms
    return re.sub(r'((?<![A-Z]{1}))[ .,;:]+(\||$)', r'\1\2', str_no_dupe_spaces)