import json
from multiprocessing import Process, Queue
import os
import requests
from time import sleep, time

from .core import CoreProcess
from managers import S3Manager, RabbitMQManager


class S3Process(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(S3Process, self).__init__(process, customFile, ingestPeriod)

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
        rabbitManager = RabbitMQManager()
        rabbitManager.createRabbitConnection()
        rabbitManager.createOrConnectQueue(fileQueue)

        bucket = os.environ['FILE_BUCKET']

        attempts = 1
        while True:
            print(rabbitManager)
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
                epubB = S3Process.getFileContents(fileURL)
                storageManager.putObjectInBucket(epubB, filePath, bucket)
                rabbitManager.acknowledgeMessageProcessed(msgProps.delivery_tag)
                print('Sending Tag {} for {}'.format(fileURL, msgProps.delivery_tag))
            except Exception as e:
                print(e)

    @staticmethod
    def getFileContents(epubURL):
        start = time()
        timeout = 90
        epubResp = requests.get(epubURL, stream=True, timeout=90)
        if epubResp.status_code == 200:
            content = bytes()
            for byteChunk in epubResp.iter_content(1024):
                print(byteChunk)
                if time() - start > timeout:
                    raise TimeoutError('Unable to process {} in time'.format(epubURL))
                content += byteChunk

            return content
        
        raise Exception('Unable to fetch ePub file')
