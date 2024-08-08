from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional


class InteractionType(Enum):
    DOWNLOAD = "Download"
    VIEW = "View"


class UsageType(Enum):
    FULL_ACCESS = "Full Access"
    LIMITED_ACCESS = "Limited Access"
    VIEW_ONLY_NO_DOWNLOAD_ACCESS = "View Only / No Download Access"


@dataclass(init=True, repr=True)
class InteractionEvent():
    title: str
    book_id: int
    authors: Optional[list[str]]
    isbns: Optional[list[str]]
    eisbns: Optional[list[str]]
    copyright_year: Optional[str]
    disciplines: Optional[list[str]]
    usage_type: UsageType
    interaction_type: InteractionType
    timestamp: str
