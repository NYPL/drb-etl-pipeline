from datetime import datetime, timedelta, timezone
from io import BytesIO
from lxml import etree
import os
import requests

from ..core import CoreProcess
from logger import createLog
from mappings.doab import DOABMapping
from mappings.core import MappingError
from managers import DOABLinkManager

logger = createLog(__name__)

class DOABProcess(CoreProcess):
    ROOT_NAMESPACE = {None: 'http://www.openarchives.org/OAI/2.0/'}

    OAI_NAMESPACES = {
        'oai_dc': 'http://www.openarchives.org/OAI/2.0/oai_dc/',
        'dc': 'http://purl.org/dc/elements/1.1/',
        'datacite': 'https://schema.datacite.org/meta/kernel-4.1/metadata.xsd',
        'oapen': 'http://purl.org/dc/elements/1.1/',
        'oaire': 'https://raw.githubusercontent.com/rcic/openaire4/master/schemas/4.0/oaire.xsd'
    }

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
        self.fileRoute = os.environ['FILE_ROUTING_KEY']
        self.createRabbitConnection()
        self.createOrConnectQueue(self.fileQueue, self.fileRoute)

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

        logger.info(f'Ingested {len(self.records)} DOAB records')

    def parseDOABRecord(self, oaiRec):
        try:
            doabRec = DOABMapping(oaiRec, self.OAI_NAMESPACES, self.statics)
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
        urlParams = 'verb=GetRecord&metadataPrefix=oai_dc&identifier=oai:directory.doabooks.org:{}'.format(recordID)
        doabURL = '{}{}'.format(os.environ['DOAB_OAI_URL'], urlParams)

        doabResponse = requests.get(doabURL, timeout=30)

        if doabResponse.status_code == 200:
            content = BytesIO(doabResponse.content)
            oaidcXML = etree.parse(content)
            oaidcRecord = oaidcXML.xpath('//oai_dc:dc', namespaces=self.OAI_NAMESPACES)[0]

            try:
                self.parseDOABRecord(oaidcRecord)
            except DOABError as e:
                logger.error(f'Error parsing DOAB record {oaidcRecord}')

    def importOAIRecords(self, fullOrPartial=False, startTimestamp=None):
        resumptionToken = None

        recordsProcessed = 0
        while True:
            oaiFile = self.downloadOAIRecords(fullOrPartial, startTimestamp, resumptionToken=resumptionToken)

            resumptionToken = self.getResumptionToken(oaiFile)

            if recordsProcessed < self.ingestOffset:
                recordsProcessed += 100
                continue

            oaidcRecords = etree.parse(oaiFile)

            for record in oaidcRecords.xpath('//oai_dc:dc', namespaces=self.OAI_NAMESPACES):
                if record is None: continue

                try:
                    self.parseDOABRecord(record)
                except DOABError as e:
                    logger.error(f'Error parsing DOAB record {record}')

            recordsProcessed += 100

            if not resumptionToken or recordsProcessed >= self.ingestLimit:
                break

    def getResumptionToken(self, oaiFile):
            try:
                oaiXML = etree.parse(oaiFile)
                return oaiXML.find('.//resumptionToken', namespaces=self.ROOT_NAMESPACE).text
            except AttributeError:
                return None

    def downloadOAIRecords(self, fullOrPartial, startTimestamp, resumptionToken=None):
        doabURL = os.environ['DOAB_OAI_URL']
        headers = {
            # Pass a user-agent header to prevent 403 unauthorized responses from DOAB
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        urlParams = 'verb=ListRecords'
        if resumptionToken:
            urlParams = '{}&resumptionToken={}'.format(urlParams, resumptionToken)
        elif fullOrPartial is False:
            if not startTimestamp:
                startTimestamp = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=24)).strftime('%Y-%m-%d')
            urlParams = '{}&metadataPrefix=oai_dc&from={}'.format(urlParams, startTimestamp)
        else:
            urlParams = '{}&metadataPrefix=oai_dc'.format(urlParams)

        doabURL = '{}{}'.format(doabURL, urlParams)

        doabResponse = requests.get(doabURL, stream=True, timeout=30, headers=headers)

        if doabResponse.status_code == 200:
            content = bytes()

            for chunk in doabResponse.iter_content(1024 * 100): content += chunk

            return BytesIO(content)

        raise DOABError(f'Received {doabResponse.status_code} status code from {doabURL}')

    def createManifestInS3(self, manifestPath, manifestJSON):
        self.putObjectInBucket(manifestJSON.encode('utf-8'), manifestPath, self.s3Bucket)

    def sendFileToProcessingQueue(self, fileURL, s3Location):
        s3Message = {
            'fileData': {
                'fileURL': fileURL,
                'bucketPath': s3Location
            }
        }
        self.sendMessageToQueue(self.fileQueue, self.fileRoute, s3Message)


class DOABError(Exception):
    def __init__(self, message):
        self.message = message
