import json
import os

from logger import create_log
from managers import DBManager, RabbitMQManager
from model import Record
from .. import utils

logger = create_log(__name__)


class RedriveRecordsProcess:

    def __init__(self, *args):
        self.params = utils.parse_process_args(*args)

        self.db_manager = DBManager()
        self.db_manager.createSession()

        self.records_queue = os.environ.get('RECORD_PIPELINE_QUEUE')
        self.records_route = os.environ.get('RECORD_PIPELINE_ROUTING_KEY')

        self.rabbitmq_manager = RabbitMQManager()
        self.rabbitmq_manager.createRabbitConnection()
        self.rabbitmq_manager.createOrConnectQueue(queueName=self.records_queue, routingKey=self.records_route)

    def runProcess(self):
        try:
            source_ids = (
                self.db_manager.session.query(Record.source_id)
                    .filter(Record.source == self.params.source)
                    .yield_per(1000)
            )

            for source_id, *_ in source_ids:
                self.rabbitmq_manager.sendMessageToQueue(
                    queueName=self.records_queue, 
                    routingKey=self.records_route, 
                    message=json.dumps({ 'source': self.params.source, 'sourceId': source_id })
                )

            logger.info(f'Redrove records for source: {self.params.source}')
        except Exception as e:
            logger.info(f'Failed to redrive records for source: {self.params.source}')
        finally:
            self.db_manager.close_connection()
            self.rabbitmq_manager.closeRabbitConnection()
