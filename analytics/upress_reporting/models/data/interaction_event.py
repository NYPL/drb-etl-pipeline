from dataclasses import dataclass
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
    country: Optional[str]
    title: str
    book_id: int
    authors: str
    isbns: str
    copyright_year: Optional[str]
    publication_year: Optional[str]
    disciplines: Optional[str]
    usage_type: str
    interaction_type: InteractionType
    timestamp: str
