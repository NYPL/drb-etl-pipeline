import os

from logger import create_log
from managers import DBManager, RabbitMQManager
from model import Record
from services.sources.source_service import SourceService
from  .record_buffer import RecordBuffer
from . import utils

logger = create_log(__name__)


class RecordIngestor():

    def __init__(self, source_service: SourceService, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.record_buffer = RecordBuffer(db_manager=self.db_manager)

        self.record_pipeline_queue = os.environ.get('RECORD_PIPELINE_QUEUE')
        self.record_pipeline_route = os.environ.get('RECORD_PIPEPELINE_ROUTING_KEY')

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.record_pipeline_route, self.record_pipeline_queue)

        self.source_service = source_service

    def ingest(self) -> int:
        try:
            records = self.source_service.get_records(
                start_timestamp=utils.get_start_datetime(process_type=self.params.process_type, ingest_period=self.params.ingest_period),
                offset=self.params.offset,
                limit=self.params.limit
            )

            for record in records:
                self._ingest_record(record=record)

            self.record_buffer.flush()

            logger.info(f'Ingested {self.record_buffer.ingest_count} {self.params.source} records')
            return self.record_buffer.ingest_count
        except Exception:
            logger.exception(f'Failed to ingest {self.params.source} records')
        finally:
            self.db_manager.close_connection()

    def _ingest_record(self, record: Record):
        try:
            self.record_buffer.add(record)
            self.rabbitmq_manager.sendMessageToQueue(
                queueName=self.record_pipeline_queue, 
                routingKey=self.record_pipeline_route,
                message={ 'recordId': record.source_id }
            )
        except Exception:
            logger.exception(f'Failed to ingest record: {record}')
