import json
from multiprocessing import Process
import os
import requests
from time import sleep
from urllib.parse import quote_plus

from .core import CoreProcess
from managers import S3Manager, RabbitMQManager
from logger import createLog


logger = createLog(__name__)


class S3Process(CoreProcess):
    def __init__(self, *args):
        super(S3Process, self).__init__(*args[:4])

    def runProcess(self):
        self.receiveAndProcessMessages()

    def receiveAndProcessMessages(self):
        processes = 4
        epubProcesses = []
        for _ in range(processes):
            proc = Process(target=S3Process.storeFilesInS3)
            proc.start()
            epubProcesses.append(proc)

        for proc in epubProcesses:
            proc.join()

    @staticmethod
    def storeFilesInS3():
        storageManager = S3Manager()
        storageManager.createS3Client()

        fileQueue = os.environ['FILE_QUEUE']
        fileRoute = os.environ['FILE_ROUTING_KEY']
        epubConverterURL = os.environ['WEBPUB_CONVERSION_URL']

        rabbitManager = RabbitMQManager()
        rabbitManager.createRabbitConnection()
        rabbitManager.createOrConnectQueue(fileQueue, fileRoute)

        bucket = os.environ['FILE_BUCKET']

        attempts = 1
        while True:
            msgProps, _, msgBody = rabbitManager.getMessageFromQueue(fileQueue)
            if msgProps is None:
                if attempts <= 3:
                    sleep(30 * attempts)
                    attempts += 1
                    continue
                else:
                    break

            attempts = 1

            fileMeta = json.loads(msgBody)['fileData']
            fileURL = fileMeta['fileURL']
            filePath = fileMeta['bucketPath']

            try:
                logger.info('Storing {}'.format(fileURL))
                epubB = S3Process.getFileContents(fileURL)

                storageManager.putObjectInBucket(epubB, filePath, bucket)

                if '.epub' in filePath:
                    fileRoot = '.'.join(filePath.split('.')[:-1])

                    webpubManifest = S3Process.generateWebpub(
                        epubConverterURL, fileRoot, bucket
                    )

                    storageManager.putObjectInBucket(
                        webpubManifest,
                        '{}/manifest.json'.format(fileRoot),
                        bucket
                    )

                rabbitManager.acknowledgeMessageProcessed(msgProps.delivery_tag)

                logger.info('Sending Tag {} for {}'.format(fileURL, msgProps.delivery_tag))

                del epubB
            except Exception as e:
                logger.error('Unable to store file in S3')
                logger.debug(e)

    @staticmethod
    def getFileContents(epubURL):
        timeout = 15
        epubResp = requests.get(
            epubURL,
            stream=True,
            timeout=timeout,
            headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'}
        )

        if epubResp.status_code == 200:
            content = bytes()
            for byteChunk in epubResp.iter_content(1024 * 250):
                content += byteChunk

            return content

        raise Exception('Unable to fetch ePub file')

    @staticmethod
    def generateWebpub(converterRoot, fileRoot, bucket):
        s3Path = 'https://{}.s3.amazonaws.com/{}/META-INF/container.xml'.format(
            bucket, fileRoot
        )

        converterURL = '{}/api/{}'.format(converterRoot, quote_plus(s3Path))

        try:
            webpubResp = requests.get(converterURL, timeout=15)

            webpubResp.raise_for_status()

            return webpubResp.content
        except Exception as e:
            logger.warning('Unable to generate webpub')
            logger.debug(e)
