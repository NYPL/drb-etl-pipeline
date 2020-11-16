import json
import os
import requests
from time import sleep

from .core import CoreProcess


class EpubProcess(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(EpubProcess, self).__init__(process, customFile, ingestPeriod)

        # Create RabbitMQ Connection
        self.createRabbitConnection()
        self.createChannel()

        # Create S3 Connection
        self.createS3Client()
        self.bucket = os.environ['EPUB_BUCKET']
    
    def runProcess(self):
        self.receiveAndProcessMessages()

    def receiveAndProcessMessages(self):
        attempts = 1
        while True:
            msgProps, msgParams, msgBody = self.getMessageFromQueue(os.environ[''])
            if msgProps is None:
                if attempts <= 3:
                    sleep(30 * attempts)
                    attempts += 1
                    continue
                else:
                    break
            
            attempts = 1

            self.storeEpubFile(msgBody)
            self.acknowledgeMessageProcessed(msgProps.delivery_tag)
    
    def storeEpubFile(self, msg):
        epubMeta = json.loads(msg)['epubURL']
        epubURL = epubMeta['epubURL']
        epubPath = epubMeta['bucketPath']
        epubB = self.getFileContents(epubURL)

        self.putObjectInBucket(epubB, epubPath, self.bucket)
    
    def getFileContents(self, epubURL):
        epubResp = requests.get(epubURL)
        if epubResp.status_code == 200:
            return epubResp.content
        
        raise Exception('Unable to fetch ePub file')
