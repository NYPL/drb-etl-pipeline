from dataclasses import dataclass

@dataclass(init=True, repr=True)
class DownloadEvent():
    title: str
    timestamp: str
    edition_id: int
