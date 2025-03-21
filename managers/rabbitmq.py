import json
from pika import BlockingConnection, ConnectionParameters
from pika.credentials import PlainCredentials
from pika.exceptions import ConnectionWrongStateError, StreamLostError, ChannelClosedByBroker
import os

from logger import create_log

logger = create_log(__name__)


class RabbitMQManager:
    def __init__(
        self, 
        host=None, 
        port=None, 
        virtual_host=None,
        exchange=None, 
        user=None, 
        pswd=None,
        queue_name=None, 
        routing_key=None,
    ):
        super(RabbitMQManager, self).__init__()
        self.rabbitHost = host or os.environ.get('RABBIT_HOST', None)
        self.rabbitPort = port or os.environ.get('RABBIT_PORT', None)
        self.rabbitVirtualHost = virtual_host or os.environ.get('RABBIT_VIRTUAL_HOST', None)
        self.rabbitExchange = exchange or os.environ.get('RABBIT_EXCHANGE', None)

        self.rabbitUser = user or os.environ.get('RABBIT_USER', None)
        self.rabbitPswd = pswd or os.environ.get('RABBIT_PSWD', None)

        self.queue_name = queue_name
        self.routing_key = routing_key

    def __enter__(self):
        self.createRabbitConnection()
        self.createOrConnectQueue(queueName=self.queue_name, routingKey=self.routing_key)

        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        self.closeRabbitConnection()
    
    def createRabbitConnection(self):
        paramDict = {
            'host': self.rabbitHost, 'port': self.rabbitPort, 'heartbeat': 600
        }

        if self.rabbitVirtualHost:
            paramDict['virtual_host'] = self.rabbitVirtualHost

        if self.rabbitUser and self.rabbitPswd:
            paramDict['credentials'] = self.createRabbitCredentials() 

        params = ConnectionParameters(**paramDict)

        self.rabbitConn = BlockingConnection(params)

    def createRabbitCredentials(self):
        return PlainCredentials(self.rabbitUser, self.rabbitPswd)
        
    def closeRabbitConnection(self):
        self.rabbitConn.close()
    
    def createChannel(self):
        self.channel = self.rabbitConn.channel()
    
    def createOrConnectQueue(self, queueName, routingKey):
        self.createChannel()
        self.channel.queue_declare(queue=queueName, durable=True)

        if self.rabbitExchange:
            self.channel.queue_bind(
                exchange=self.rabbitExchange,
                queue=queueName,
                routing_key=routingKey
            )
    
    def sendMessageToQueue(self, queueName, routingKey, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        
        try:
            self.channel.basic_publish(
                exchange=self.rabbitExchange,
                routing_key=routingKey,
                body=message
            )
        except (ConnectionWrongStateError, StreamLostError):
            logger.debug('Stale RabbitMQ connection - reconnecting.')
            # Connection timed out. Reconnect and try again
            self.createRabbitConnection()
            self.createOrConnectQueue(queueName, routingKey)
            self.sendMessageToQueue(queueName, routingKey, message)

    
    def getMessageFromQueue(self, queueName):
        try:
            return self.channel.basic_get(queueName)
        except (ConnectionWrongStateError, StreamLostError):
            self.createRabbitConnection()
            self.createChannel()
            return self.getMessageFromQueue(queueName)
        except ChannelClosedByBroker:
            self.createRabbitConnection()
            self.createChannel()

        return None
    
    def acknowledgeMessageProcessed(self, deliveryTag):
        try:
            self.channel.basic_ack(deliveryTag)
        except (ConnectionWrongStateError, StreamLostError):
            self.createRabbitConnection()
            self.createChannel()
            self.acknowledgeMessageProcessed(deliveryTag)

    def reject_message(self, delivery_tag: str, requeue=False):
        try:
            self.channel.basic_reject(delivery_tag=delivery_tag, requeue=requeue)
        except (ConnectionWrongStateError, StreamLostError):
            self.createRabbitConnection()
            self.createChannel()
            self.reject_message(delivery_tag, requeue)      
