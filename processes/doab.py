from datetime import datetime, timedelta
from io import BytesIO
from lxml import etree
import os
from pymarc import parse_xml_to_array
import requests

from .core import CoreProcess
from mappings.doab import DOABMapping
from mappings.core import MappingError
from managers import DOABLinkManager


class DOABProcess(CoreProcess):
    OAI_NS = '{http://www.openarchives.org/OAI/2.0/}'

    def __init__(self, *args):
        super(DOABProcess, self).__init__(*args[:4])

        self.ingestOffset = int(args[5]) if args[5] else 0
        self.ingestLimit = (int(args[4]) + self.ingestOffset) if args[4] else 10000

        self.generateEngine()
        self.createSession()

        self.createS3Client()
        self.s3Bucket = os.environ['FILE_BUCKET']

        # Connect to epub processing queue
        self.fileQueue = os.environ['FILE_QUEUE']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.fileQueue)

    def runProcess(self):
        if self.process == 'daily':
            self.importOAIRecords()
        elif self.process == 'complete':
            self.importOAIRecords(fullOrPartial=True)
        elif self.process == 'custom':
            self.importOAIRecords(startTimestamp=self.ingestPeriod)
        elif self.process == 'single':
            self.importSingleOAIRecord(self.singleRecord)

        self.saveRecords()
        self.commitChanges()
    
    def parseDOABRecord(self, marcRec):
        try:
            doabRec = DOABMapping(marcRec, self.statics)
            doabRec.applyMapping()
        except MappingError as e:
            raise DOABError(e.message)

        linkManager = DOABLinkManager(doabRec.record)
        
        linkManager.parseLinks()

        for manifest in linkManager.manifests:
            manifestPath, manifestJSON = manifest
            self.createManifestInS3(manifestPath, manifestJSON)

        for epubLink in linkManager.ePubLinks:
            ePubPath, ePubURI = epubLink
            self.sendFileToProcessingQueue(ePubURI, ePubPath)

        self.addDCDWToUpdateList(doabRec)

    def importSingleOAIRecord(self, recordID):
        urlParams = 'verb=GetRecord&metadataPrefix=marcxml&identifier=oai:doab-books:{}'.format(recordID)
        doabURL = '{}{}'.format(os.environ['DOAB_OAI_URL'], urlParams)

        doabResponse = requests.get(doabURL, timeout=30, verify=False)

        if doabResponse.status_code == 200:
            content = BytesIO(doabResponse.content)
            marcRecord = parse_xml_to_array(content)[0]

            try:
                self.parseDOABRecord(marcRecord)
            except DOABError as e:
                print('ERROR', e)
    
    def importOAIRecords(self, fullOrPartial=False, startTimestamp=None):
        resumptionToken = None

        recordsProcessed = 0
        while True:
            oaiFile = self.downloadOAIRecords(fullOrPartial, startTimestamp, resumptionToken=resumptionToken)

            resumptionToken = self.getResumptionToken(oaiFile)

            if recordsProcessed < self.ingestOffset:
                recordsProcessed += 100
                continue
            
            marcReader = parse_xml_to_array(oaiFile)

            for record in marcReader:
                if record is None: continue

                try:
                    self.parseDOABRecord(record)
                except DOABError as e:
                    print('ERROR', e)

            recordsProcessed += 100

            if not resumptionToken or recordsProcessed >= self.ingestLimit:
                break

    def getResumptionToken(self, oaiFile):
            try:
                oaiXML = etree.parse(oaiFile)
                return oaiXML.find('.//{}resumptionToken'.format(self.OAI_NS)).text
            except AttributeError:
                return None

    def downloadOAIRecords(self, fullOrPartial, startTimestamp, resumptionToken=None):
        doabURL = os.environ['DOAB_OAI_URL']

        urlParams = 'verb=ListRecords'
        if resumptionToken:
            urlParams = '{}&resumptionToken={}'.format(urlParams, resumptionToken)
        elif fullOrPartial is False:
            if not startTimestamp:
                startTimestamp = (datetime.utcnow() - timedelta(hours=24)).strftime('%Y-%m-%d')
            urlParams = '{}&metadataPrefix=marcxml&from={}'.format(urlParams, startTimestamp)
        else:
            urlParams = '{}&metadataPrefix=marcxml'.format(urlParams)

        doabURL = '{}{}'.format(doabURL, urlParams)
            
        doabResponse = requests.get(doabURL, stream=True, timeout=30, verify=False)

        if doabResponse.status_code == 200:
            content = bytes()

            for chunk in doabResponse.iter_content(1024 * 100): content += chunk

            return BytesIO(content)

        raise DOABError('Unable to load Project MUSE MARC file')

    def createManifestInS3(self, manifestPath, manifestJSON):
        self.putObjectInBucket(manifestJSON.encode('utf-8'), manifestPath, self.s3Bucket)
    
    def sendFileToProcessingQueue(self, fileURL, s3Location):
        s3Message = {
            'fileData': {
                'fileURL': fileURL,
                'bucketPath': s3Location
            }
        }
        self.sendMessageToQueue(self.fileQueue, s3Message)


class DOABError(Exception):
    def __init__(self, message):
        self.message = message
