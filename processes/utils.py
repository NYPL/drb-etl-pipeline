from datetime import datetime, timedelta, timezone
from typing import Optional


def get_start_datetime(process_type: Optional[str]=None, ingest_period: Optional[str]=None) -> Optional[str]:
    if ingest_period is not None:
        return datetime.strptime(ingest_period, '%Y-%m-%dT%H:%M:%S')

    if process_type == 'daily':
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)
    
    if process_type == 'weekly':
        return datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)
    
    return None
