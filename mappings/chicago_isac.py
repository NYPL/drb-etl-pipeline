import dataclasses
from datetime import datetime, timezone
import json
from typing import Optional
from uuid import uuid4

from model import Record, FRBRStatus, FileFlags


def map_chicago_isac_record(record: dict) -> Record:
    pdf_flags = FileFlags(download=True)

    isbns = get_isbns(record)

    if isbns is None:
        raise Exception(f'Failed to get ISBN')
    
    return Record(
        uuid=uuid4(),
        frbr_status=FRBRStatus.TODO.value,
        cluster_status=False,
        source='isac',
        source_id=f'isac_{isbns[0]}',
        title=record.get('title'),
        authors=[f'{author}|||true' for author in record.get('authors', []) if author],
        publisher=record.get('publisher'),
        identifiers=[f'{isbn}|isbn' for isbn in isbns],
        is_part_of=f"{record.get('series')}|series" if record.get('series') else None,
        spatial=record.get('publisherLocation'),
        extent=record.get('extent'),
        has_part=[f"1|{record.get('url')[0]}|isac|application/pdf|{json.dumps(dataclasses.asdict(pdf_flags))}"],
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )


def get_isbns(record: dict) -> Optional[list[str]]:
    isbn = record.get('isbn')

    if not isbn:
        return None
    
    if ',' in isbn:
        return [isbn.strip() for isbn in isbn.split(',')]
    
    return [isbn]
