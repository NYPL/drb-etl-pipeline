import os

from managers import RabbitMQManager, S3Manager
from model import get_file_message
from processes import S3Process

TEST_SOURCE_FILE_NAME = 'tests/source-pdf.pdf'
TEST_PROCESSED_FILE_NAME = 'tests/processed-pdf.pdf'


def test_s3_process(rabbitmq_manager: RabbitMQManager, s3_manager: S3Manager):
    file_queue = os.environ['FILE_QUEUE']
    file_route = os.environ['FILE_ROUTING_KEY']
    file_bucket = os.environ['FILE_BUCKET']

    rabbitmq_manager.create_or_connect_queue(file_queue, file_route)

    s3_manager.putObjectInBucket(bytes(), TEST_SOURCE_FILE_NAME, file_bucket)
    file_url = f'http://localhost:4566/{file_bucket}/{TEST_SOURCE_FILE_NAME}'

    rabbitmq_manager.send_message_to_queue(
        queue_name=file_queue,
        routing_key=file_route,
        message=get_file_message(file_url=file_url, bucket_path=TEST_PROCESSED_FILE_NAME)
    )

    s3_process = S3Process()

    s3_process.runProcess(max_poll_attempts=1)

    processed_file = s3_manager.getObjectFromBucket(TEST_PROCESSED_FILE_NAME, file_bucket)

    assert processed_file is not None
    
    s3_manager.s3Client.delete_object(Bucket=file_bucket, Key=TEST_SOURCE_FILE_NAME)
    s3_manager.s3Client.delete_object(Bucket=file_bucket, Key=TEST_PROCESSED_FILE_NAME)
