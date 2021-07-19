import json
from lxml import etree
import os
from time import sleep

from .core import CoreProcess
from managers import OCLCCatalogManager
from mappings.oclcCatalog import CatalogMapping


class CatalogProcess(CoreProcess):
    def __init__(self, *args):
        super(CatalogProcess, self).__init__(*args[:4], batchSize=50)

        # PostgreSQL Connection
        self.generateEngine()
        self.createSession()

        # RabbitMQ Connection
        self.createRabbitConnection()
        self.createChannel()

    def runProcess(self):
        self.receiveAndProcessMessages()

        self.saveRecords()
        self.commitChanges()

    def receiveAndProcessMessages(self):
        attempts = 1
        while True:
            msgProps, _, msgBody = self.getMessageFromQueue(os.environ['OCLC_QUEUE'])
            if msgProps is None:
                if attempts <= 3:
                    sleep(60 * attempts)
                    attempts += 1
                    continue
                else:
                    break
            
            attempts = 1

            self.processCatalogQuery(msgBody)
            self.acknowledgeMessageProcessed(msgProps.delivery_tag)

    def processCatalogQuery(self, msgBody):
        message = json.loads(msgBody)
        catalogManager = OCLCCatalogManager(message['oclcNo'])
        catalogXML = catalogManager.queryCatalog()
        if catalogXML:
            self.parseCatalogRecord(catalogXML, message['owiNo'])

    def parseCatalogRecord(self, catalogXML, owiNo):
        try:
            parseMARC = etree.fromstring(catalogXML.encode('utf-8'))
        except etree.XMLSyntaxError as err:
            print('OCLC Catalog returned invalid XML')
            print(err)
            return None
        
        catalogRec = CatalogMapping(
            parseMARC,
            {'oclc': 'http://www.loc.gov/MARC21/slim'},
            {}
        )

        try:
            catalogRec.applyMapping()
            catalogRec.record.identifiers.append('{}|owi'.format(owiNo))
            self.addDCDWToUpdateList(catalogRec)
        except Exception as err:
            print(err)
            print('Err querying OCLC Rec {}'.format(catalogRec.record.source_id))
