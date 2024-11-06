from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from mappings.abstractMapping import AbstractMapping

class SourceService(ABC):

    @abstractmethod
    def get_records(
        self,
        full_import: bool=False,
        start_timestamp: Optional[datetime]=None,
        offset: Optional[int]=None,
        limit: Optional[int]=None
    ) -> list[AbstractMapping]:
        pass
