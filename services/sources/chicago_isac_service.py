from datetime import datetime
import json
from typing import Generator, Optional

from mappings.chicago_isac import map_chicago_isac_record
from model import Record
from .source_service import SourceService


class ChicagoISACService(SourceService):

    def get_records(
        self, 
        full_import: bool = False, 
        start_timestamp: Optional[datetime] = None, 
        offset: int = 0, 
        limit: Optional[int] = None
    ) -> Generator[Record, None, None]:
        with open('ingestJSONFiles/chicagoISAC_metadata.json') as f:
            chicago_isac_data = json.load(f)

        for record_data in chicago_isac_data:
            record = map_chicago_isac_record(record=record_data)

            if record:
                yield record
