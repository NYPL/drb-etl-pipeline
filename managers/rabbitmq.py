import json
from pika import BlockingConnection, ConnectionParameters
from pika.exceptions import ConnectionWrongStateError, StreamLostError
import os

class RabbitMQManager:
    def __init__(self, host=None, port=None):
        super(RabbitMQManager, self).__init__()
        self.rabbitHost = host or os.environ['RABBIT_HOST']
        self.rabbitPort = port or os.environ['RABBIT_PORT']
    
    def createRabbitConnection(self):
        params = ConnectionParameters(
            host=self.rabbitHost,
            port=self.rabbitPort,
            heartbeat=600
        )
        self.rabbitConn = BlockingConnection(params)
    
    def closeRabbitConnection(self):
        self.rabbitConn.close()
    
    def createChannel(self):
        self.channel = self.rabbitConn.channel()
    
    def createOrConnectQueue(self, queueName):
        self.createChannel()
        self.channel.queue_declare(queue=queueName)
    
    def sendMessageToQueue(self, queueName, message):
        if isinstance(message, dict):
            message = json.dumps(message)
        
        try:
            self.channel.basic_publish(
                exchange='', routing_key=queueName, body=message
            )
        except (ConnectionWrongStateError, StreamLostError):
            print('Stale connection. Trying to reconnect')
            # Connection timed out. Reconnect and try again
            self.createRabbitConnection()
            self.createOrConnectQueue(queueName)
            self.sendMessageToQueue(queueName, message)

    
    def getMessageFromQueue(self, queueName):
        return self.channel.basic_get(queueName)
    
    def acknowledgeMessageProcessed(self, deliveryTag):
        self.channel.basic_ack(deliveryTag)
