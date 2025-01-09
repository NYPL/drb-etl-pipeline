import json
from multiprocessing import Process
import os
import requests
from time import sleep
from urllib.parse import quote_plus

from ..core import CoreProcess
from managers import S3Manager, RabbitMQManager
from logger import create_log
from utils import retry_request


logger = create_log(__name__)


class S3Process(CoreProcess):
    def __init__(self, *args):
        super(S3Process, self).__init__(*args[:4])

    def runProcess(self):
        try:
            number_of_processes = 4
            file_processes = []

            for _ in range(number_of_processes):
                file_process = Process(target=S3Process.process_files)
                file_process.start()

                file_processes.append(file_process)

            for file_process in file_processes:
                file_process.join()
        except Exception:
            logger.exception('Failed to run S3 Process')

    @staticmethod
    def process_files():
        storage_manager = S3Manager()
        storage_manager.createS3Client()

        file_queue = os.environ['FILE_QUEUE']
        file_route = os.environ['FILE_ROUTING_KEY']

        rabbit_mq_manager = RabbitMQManager()
        rabbit_mq_manager.createRabbitConnection()
        rabbit_mq_manager.createOrConnectQueue(file_queue, file_route)

        s3_file_bucket = os.environ['FILE_BUCKET']

        attempts_to_poll = 1
        max_poll_attempts = 3

        while attempts_to_poll <= max_poll_attempts:
            message_props, _, message_body = rabbit_mq_manager.getMessageFromQueue(file_queue)

            if not message_props:
                if attempts_to_poll <= max_poll_attempts:
                    wait_time = attempts_to_poll * 30

                    logger.info(f'Waiting {wait_time}s for S3 file messages')
                    sleep(wait_time)
                    
                    attempts_to_poll += 1
                else:
                    logger.info('Exiting S3 process - no more messages.')
                    break

                continue
            
            attempts_to_poll = 1

            file_data = json.loads(message_body)['fileData']
            file_url = file_data['fileURL']
            file_path = file_data['bucketPath']

            try:
                file_contents = S3Process.get_file_contents(file_url)

                storage_manager.putObjectInBucket(file_contents, file_path, s3_file_bucket)
                
                del file_contents

                if '.epub' in file_path:
                    file_root = '.'.join(file_path.split('.')[:-1])

                    web_pub_manifest = S3Process.generate_webpub(file_root, s3_file_bucket)

                    storage_manager.putObjectInBucket(web_pub_manifest, f'{file_root}/manifest.json', s3_file_bucket)

                rabbit_mq_manager.acknowledgeMessageProcessed(message_props.delivery_tag)

                logger.info(f'Stored file in S3 for {file_url}')
            except Exception:
                logger.exception(f'Failed to store file for file url: {file_url}')
                rabbit_mq_manager.reject_message(delivery_tag=message_props.delivery_tag)

    @staticmethod
    @retry_request()
    def get_file_contents(file_url: str):
        try:
            file_url_response = requests.get(
                file_url,
                stream=True,
                timeout=15,
                headers={ 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)' }
            )

            file_url_response.raise_for_status()

            file_contents = bytes()

            for byte_chunk in file_url_response.iter_content(1024 * 250):
                file_contents += byte_chunk

            return file_contents
        except Exception as e:
            logger.exception(f'Failed to get file contents from {file_url}')
            raise e

    @staticmethod
    @retry_request()
    def generate_webpub(file_root, bucket):
        webpub_conversion_url = 'https://epub-to-webpub.vercel.app'
        s3_file_path = f'https://{bucket}.s3.amazonaws.com/{file_root}/META-INF/container.xml'
        webpub_conversion_url = f'{webpub_conversion_url}/api/{quote_plus(s3_file_path)}'

        try:
            webpub_response = requests.get(webpub_conversion_url, timeout=15)

            webpub_response.raise_for_status()

            return webpub_response.content
        except Exception as e:
            logger.exception(f'Failed to generate webpub for {file_root}')
            raise e
