import os

from managers import RabbitMQManager


def main():
    catalog_queue = os.environ.get('OCLC_QUEUE')
    catalog_route = os.environ.get('OCLC_ROUTING_KEY')
    rabbitmq_manager = RabbitMQManager()

    rabbitmq_manager.createRabbitConnection()
    rabbitmq_manager.createOrConnectQueue(queueName=catalog_queue, routingKey=catalog_route)

    queue = rabbitmq_manager.channel.queue_declare(queue=catalog_queue, passive=True)

    print(queue.method.message_count)


if __name__ == 'main':
    main()
