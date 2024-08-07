from dataclasses import dataclass, fields
from enum import Enum
from typing import Optional

class InteractionType(Enum):
    DOWNLOAD = "Download"
    VIEW = "View"

class UsageType(Enum):
    FULL_ACCESS = "Full Access"  # openly available books, full view & download possible, no sign in required
    LIMITED_ACCESS = "Limited Access"   # limits the (full) view & download of a book to Library card holders, requires sign in
    VIEW_ONLY_NO_DOWNLOAD_ACCESS = "View Only / No Download Access" # full view without sign in possible, but disabled download option

@dataclass(init=True, repr=True)
class InteractionEvent():
    # Pull from editions table title column, e.g. "Bilder aus der deutschen Vergangenheit"
    title: str
    # Pull from records table source_id column, e.g. "mdp.39015026448137|hathi".  The ID is the first part of the string delimited by |.
    book_id: int
    # Pull from works table authors column - e.g. "[{""name"": ""Chalkhill, John, (active 1600.)"", ""viaf"": """", ""lcnaf"": """", ""primary"": """"}]"
    authors: Optional[list[str]]
    # Pull from records table identifiers column 
    isbns: Optional[list[str]]
    eisbns: Optional[list[str]]
    # Pull from editions table dates column, e.g. "[{""date"": ""2008"", ""type"": ""publication_date""}, {""date"": ""2009"", ""type"": ""publication_date""}]"
    copyright_year: Optional[str]
    # Pull from works table subjects column, e.g. "[{""heading"": ""Poetry (English)"", ""authority"": """", ""controlNo"": """"}, {""heading"": ""Livres numériques"", ""authority"": ""rvmgf"", ""controlNo"": """"}]"
    disciplines: Optional[list[str]]
    # Pull from records table rights column, e.g. "hathitrust|public_domain|copyright renewal research was conducted|Public Domain|2011-08-24 05:30:05"
    usage_type: UsageType
    interaction_type: InteractionType
    timestamp: str