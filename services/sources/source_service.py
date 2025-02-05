from abc import ABC, abstractmethod
from datetime import datetime
from typing import Generator, Optional, Union

from mappings.record_mapping import RecordMapping

class SourceService(ABC):

    @abstractmethod
    def get_records(
        self,
        full_import: bool=False,
        start_timestamp: Optional[datetime]=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> Union[list[RecordMapping], Generator[RecordMapping, None, None]]:
        pass
