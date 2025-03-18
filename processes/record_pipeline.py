

'''
High-Level Flow:

1. Ingestors get and map records and send message to record pipeline queue
2. Record pipeline process processes messages from the queue
3. For each message, the record pipeline stores the files, frbrizes and clusters the record
4. Optionally, the process fulfills the links

Pros: 
- Scalability: We can spin up n tasks to process messages from the queue. 
- Simplicity: Removes potentially 4 processes and ECS tasks
- Testability: Possible to test 
- Observability/Debuggability: Easier to see where a record fails to be processed in the pipeline
- State Management: We can ensure the database state fields truthfully match the state of a record. 
'''

import json
import os

from .record_frbrizer import RecordFRBRizer
from .record_clusterer import RecordClusterer
from .link_fulfiller import LinkFulfiller

from logger import create_log
from managers import DBManager, RabbitMQManager
from model import Record

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
        while message := self.rabbitmq_manager.getMessageFromQueue(self.record_queue):
            message_props, _, message_body = message

            if not message_props or not message_body:
                break

            source_id, source = self._process_message(message_body=message_body)

            try:
                record = self.db_manager.session.query(Record)\
                    .filter(Record.source_id == source_id, Record.source == source).first()

                frbrized_record = self.record_frbrizer.frbrize_record(record)

                clustered_records = self.record_clusterer.cluster_record(frbrized_record)

                self.link_fulfiller.fulfill_records_links(clustered_records)
                    
                self.rabbitmq_manager.acknowledgeMessage(message_props.delivery_tag)
            except Exception:
                logger.exception(f'Failed to process record with source_id: {source_id} and source: {source}')
                self.rabbitmq_manager.reject_message(delivery_tag=message_props.delivery_tag)
            

    def _process_message(self, message_body) -> Record:
        message = json.loads(message_body)

        source_id = message.get('sourceId')
        source = message.get('source')

        return source_id, source