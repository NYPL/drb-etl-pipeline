import os
import sys

from managers import RabbitMQManager

'''
Usage:  python main.py --script checkQueueSize -e <env> options queueName=<queueName> routingKey=<routingKey>
'''

def main(*args):
    queue_name_arg = next(filter(lambda option: option.startswith('queueName'), args), None)
    routing_key_arg = next(filter(lambda option: option.startswith('routingKey'), args), None)
    queue_name = queue_name_arg.split('=')[1] if queue_name_arg else os.environ.get('RECORD_PIPELINE_QUEUE')
    routing_key = routing_key_arg.split('=')[1] if routing_key_arg else os.environ.get('RECORD_PIPELINE_ROUTING_KEY')

    try:
        rabbitmq_manager = RabbitMQManager()

        rabbitmq_manager.createRabbitConnection()
        rabbitmq_manager.createOrConnectQueue(queueName=queue_name, routingKey=routing_key)

        queue = rabbitmq_manager.channel.queue_declare(queue=queue_name, passive=True)

        print(f'{queue.method.message_count} messages in {queue_name} queue')
    except Exception:
        print(f'Unable to get message count for {queue_name} queue')

if __name__ == 'main':
    args = sys.argv[1:]
    main(*args)
