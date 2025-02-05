from datetime import datetime, timezone
from uuid import uuid4

from model import Record, FRBRStatus, Source


def map_to_record(source_record: dict, source: Source) -> Record:
    return Record(
        uuid=uuid4(),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None),
        frbr_status=FRBRStatus.TODO.value,
        cluster_status=False,
        source=source.value,
        **source_record
    )
