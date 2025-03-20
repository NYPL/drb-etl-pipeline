import json
import os

from .record_frbrizer import RecordFRBRizer
from .record_clusterer import RecordClusterer
from .link_fulfiller import LinkFulfiller

from logger import create_log
from managers import DBManager, RabbitMQManager
from model import Record
from concurrent.futures import ThreadPoolExecutor, TimeoutError

logger = create_log(__name__)


class RecordPipelineProcess:

    def __init__(self, *args):
        self.db_manager = DBManager()
        self.db_manager.generateEngine()
        self.db_manager.createSession()

        self.record_queue = os.environ['RECORD_PIPELINE_QUEUE']
        self.record_route = os.environ['RECORD_PIPELINE_ROUTING_KEY']

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(self.record_queue, self.record_route)

        self.record_frbrizer = RecordFRBRizer(db_manager=self.db_manager)
        self.record_clusterer = RecordClusterer(db_manager=self.db_manager)
        self.link_fulfiller = LinkFulfiller(db_manager=self.db_manager)

    def runProcess(self):
        try:
            while message := self.rabbitmq_manager.getMessageFromQueue(self.record_queue):
                message_props, _, message_body = message

                if not message_props or not message_body:
                    break
                
                self._process_message(message)
        except Exception:
            logger.exception('Failed to run record pipeline process')
        finally:
            self.db_manager.close_connection()
            self.rabbitmq_manager.closeRabbitConnection()
    
    def _process_message(self, message):
        try:
            message_props, _, message_body = message
            source_id, source = self._parse_message(message_body=message_body)

            record = (
                self.db_manager.session.query(Record)
                    .filter(Record.source_id == source_id, Record.source == source)
                    .first()
            )

            frbrized_record = self.record_frbrizer.frbrize_record(record)
            clustered_records = self._cluster_record_with_timeout(frbrized_record, timeout=60)
            self.link_fulfiller.fulfill_records_links(clustered_records)
                
            self.rabbitmq_manager.acknowledgeMessageProcessed(message_props.delivery_tag)
        except Exception:
            logger.exception(f'Failed to process record with source_id: {source_id} and source: {source}')            
            self.rabbitmq_manager.reject_message(delivery_tag=message_props.delivery_tag)

    def _parse_message(self, message_body) -> tuple:
        message = json.loads(message_body)

        source_id = message.get('sourceId')
        source = message.get('source')

        return source_id, source
    
    def _cluster_record_with_timeout(self, frbrized_record, timeout):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self.record_clusterer.cluster_record, frbrized_record)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                raise TimeoutError(f"Clustering process timed out after {timeout} seconds for {frbrized_record}")