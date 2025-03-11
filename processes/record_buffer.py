import os
from typing import Optional

from managers import DBManager, RabbitMQManager
from model import Record, FRBRStatus


class RecordBuffer:
    def __init__(self, db_manager: DBManager, rabbitmq_manager: Optional[RabbitMQManager]=None, batch_size: int=500):
        self.db_manager = db_manager
        self.rabbitmq_manager = rabbitmq_manager

        self.record_pipeline_queue = os.environ.get('RECORD_PIPELINE_QUEUE')
        self.record_pipeline_route = os.environ.get('RECORD_PIPEPELINE_ROUTING_KEY')

        self.records = set()
        self.batch_size = batch_size
        self.ingest_count = 0
        self.deletion_count = 0

    def add(self, record: Record):
        existing_record = self.db_manager.session.query(Record).filter(
            Record.source_id == record.source_id
        ).first()

        if existing_record:
            existing_record = self._update_record(record, existing_record)
            self.records.discard(existing_record)
            self.records.add(existing_record)
        else:
            self.records.add(record)

        if len(self.records) > self.batch_size:
            self.flush()

    # TODO: Implement deletion for the rest of the FRBR model
    def delete(self, record: Record):
        existing_record = self.db_manager.session.query(Record).filter(
            Record.source_id == record.source_id
        ).first()

        if existing_record:
            self.db_manager.session.delete(existing_record)
            self.deletion_count += 1
            self.db_manager.session.commit()

    def flush(self):
        self.db_manager.bulkSaveObjects(self.records)

        if self.rabbitmq_manager is not None:
            for record in self.records:
                self.rabbitmq_manager.sendMessageToQueue(
                    queueName=self.record_pipeline_queue, 
                    routingKey=self.record_pipeline_route,
                    message={ 'recordId': record.source_id }
                )

        self.ingest_count += len(self.records)
        self.records.clear()

    def _update_record(self, record: Record, existing_record: Record) -> Record:
        for attribute, value in record:
            if attribute == 'uuid': 
                continue

            setattr(existing_record, attribute, value)
        
        existing_record.cluster_status = False
        
        if existing_record.source not in ['oclcClassify', 'oclcCatalog']:
            existing_record.frbr_status = FRBRStatus.TODO.value

        return existing_record
