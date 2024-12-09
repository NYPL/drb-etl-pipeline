from managers import DBManager
from mappings.base_mapping import BaseMapping
from model import Record

class RecordBuffer:
    def __init__(self, db_manager: DBManager, batch_size: int=500):
        self.db_manager = db_manager
        self.records = set()
        self.batch_size = batch_size
        self.ingest_count = 0

    def add(self, record_mapping: BaseMapping):
        existing_record = self.db_manager.session.query(Record).filter(
            Record.source_id == record_mapping.record.source_id
        ).first()

        if existing_record:
            record_mapping.updateExisting(existing_record)
            self.records.discard(existing_record)
            self.records.add(existing_record)
        else:
            self.records.add(record_mapping.record)

        if self.batch_size >= len(self.records):
            self.flush()

    def flush(self):
        self.db_manager.bulkSaveObjects(self.records)
        self.ingest_count += len(self.records)
        self.records.clear()
