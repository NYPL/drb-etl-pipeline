import json
import os
import requests
from time import sleep

from .core import CoreProcess


class S3Process(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(S3Process, self).__init__(process, customFile, ingestPeriod)

        # Create RabbitMQ Connection
        self.createRabbitConnection()
        self.createChannel()

        # Create S3 Connection
        self.createS3Client()
        self.bucket = os.environ['FILE_BUCKET']
    
    def runProcess(self):
        self.receiveAndProcessMessages()

    def receiveAndProcessMessages(self):
        attempts = 1
        while True:
            msgProps, msgParams, msgBody = self.getMessageFromQueue(os.environ['FILE_QUEUE'])
            if msgProps is None:
                if attempts <= 3:
                    sleep(30 * attempts)
                    attempts += 1
                    continue
                else:
                    break
            
            attempts = 1

            self.storeFileInS3(msgBody)
            self.acknowledgeMessageProcessed(msgProps.delivery_tag)
    
    def storeFileInS3(self, msg):
        fileMeta = json.loads(msg)['fileData']
        fileURL = fileMeta['fileURL']
        filePath = fileMeta['bucketPath']
        epubB = self.getFileContents(fileURL)

        self.putObjectInBucket(epubB, filePath, self.bucket)
    
    def getFileContents(self, epubURL):
        epubResp = requests.get(epubURL)
        if epubResp.status_code == 200:
            return epubResp.content
        
        raise Exception('Unable to fetch ePub file')
