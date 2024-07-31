from dataclasses import dataclass
from enum import Enum
from typing import Optional

class InteractionType(Enum):
    DOWNLOAD = 'Download'
    VIEW = 'View'

@dataclass(init=True, repr=True)
class InteractionEvent():
    # Pull from editions table title column, e.g. "Bilder aus der deutschen Vergangenheit"
    title: str
    # Pull from records table source_id column, e.g. "mdp.39015026448137|hathi".  The ID is the first part of the string delimited by |.
    book_id: int
    # Pull from works table authors column - e.g. "[{""name"": ""Chalkhill, John, (active 1600.)"", ""viaf"": """", ""lcnaf"": """", ""primary"": """"}]"
    authors: Optional[list[str]]
    # Pull from records table identifiers column - e.g. 
    isbn: Optional[str]
    eisbn: Optional[str]
    # Pull from editions table dates column, e.g. "[{""date"": ""2008"", ""type"": ""publication_date""}, {""date"": ""2009"", ""type"": ""publication_date""}]"
    copyright_year: Optional[str]
    # Pull from works table subjects column, e.g. "[{""heading"": ""Poetry (English)"", ""authority"": """", ""controlNo"": """"}, {""heading"": ""Livres numériques"", ""authority"": ""rvmgf"", ""controlNo"": """"}]"
    disciplines: Optional[list[str]]
    # Pull from records rights column, e.g. "hathitrust|public_domain|copyright renewal research was conducted|Public Domain|2011-08-24 05:30:05"
    usage_type: Optional[str]
    interaction_type: InteractionType
    timestamp: str
