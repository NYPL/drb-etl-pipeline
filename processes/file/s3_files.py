import json
from multiprocessing import Process
import os
import requests
from time import sleep
from urllib.parse import quote_plus

from managers import S3Manager, RabbitMQManager
from logger import create_log
from utils import retry_request


logger = create_log(__name__)


class S3Process():
    WEBPUB_CONVERSION_BASE_URL = 'https://epub-to-webpub.vercel.app'

    def __init__(self, *args):
        pass

    def runProcess(self, max_poll_attempts: int=4):
        try:
            number_of_processes = 4
            file_processes = []

            for _ in range(number_of_processes):
                file_process = Process(target=S3Process.process_files, args=(max_poll_attempts,))
                file_process.start()

                file_processes.append(file_process)

            for file_process in file_processes:
                file_process.join()
        except Exception:
            logger.exception('Failed to run S3 Process')

    @staticmethod
    def process_files(max_poll_attempts: int):
        storage_manager = S3Manager()

        file_queue = os.environ['FILE_QUEUE']
        file_route = os.environ['FILE_ROUTING_KEY']

        rabbit_mq_manager = RabbitMQManager()
        rabbit_mq_manager.createRabbitConnection()
        rabbit_mq_manager.createOrConnectQueue(file_queue, file_route)

        for poll_attempt in range(0, max_poll_attempts):
            wait_time = 30 * poll_attempt

            if wait_time:
                logger.info(f'Waiting {wait_time}s for S3 file messages')
                sleep(wait_time)

            while message := rabbit_mq_manager.getMessageFromQueue(file_queue):
                message_props, _, message_body = message

                if not message_props or not message_body:
                    break

                S3Process.process_message(
                    message=message, 
                    storage_manager=storage_manager, 
                    rabbit_mq_manager=rabbit_mq_manager
                )

    @staticmethod
    def process_message(message, storage_manager: S3Manager, rabbit_mq_manager: RabbitMQManager):
        message_props, _, message_body = message

        s3_file_bucket = os.environ['FILE_BUCKET']
        file_data = json.loads(message_body)['fileData']
        file_url = file_data['fileURL']
        file_path = file_data['bucketPath']

        try:
            file_contents = S3Process.get_file_contents(file_url)

            storage_manager.put_object(file_contents, file_path, s3_file_bucket)
            
            del file_contents

            if '.epub' in file_path:
                file_root = '.'.join(file_path.split('.')[:-1])

                web_pub_manifest = S3Process.generate_webpub(file_root, s3_file_bucket)

                storage_manager.put_object(web_pub_manifest, f'{file_root}/manifest.json', s3_file_bucket)

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
        s3_file_path = f'https://{bucket}.s3.amazonaws.com/{file_root}/META-INF/container.xml'
        webpub_conversion_url = f'{S3Process.WEBPUB_CONVERSION_BASE_URL}/api/{quote_plus(s3_file_path)}'

        try:
            webpub_response = requests.get(webpub_conversion_url, timeout=15)

            webpub_response.raise_for_status()

            return webpub_response.content
        except Exception as e:
            logger.exception(f'Failed to generate webpub for {file_root}')
            raise e
