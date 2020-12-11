from datetime import datetime, timedelta
import os
import requests

from .core import CoreProcess
from managers.db import DBManager
from mappings.nypl import NYPLMapping


class NYPLProcess(CoreProcess):
    def __init__(self, process, customFile, ingestPeriod):
        super(NYPLProcess, self).__init__(process, customFile, ingestPeriod)
        self.generateEngine()
        self.createSession()
        self.generateAccessToken()

        self.bibDBConnection = DBManager(
            user=os.environ['BIB_USER'],
            pswd=os.environ['BIB_PSWD'],
            host=os.environ['BIB_HOST'],
            port=os.environ['BIB_PORT'],
            db=os.environ['BIB_NAME']
        )
        self.bibDBConnection.generateEngine()

        self.locationCodes = self.loadLocationCodes()

    def loadLocationCodes(self):
        return requests.get(os.environ['NYPL_LOCATIONS_BY_CODE']).json()

    def isResearchBib(self, bib):
        bibStatus = self.queryApi('bibs/{}/{}/is-research'.format(
            bib['nypl_source'], bib['id']
        ))

        return True if bibStatus['isResearch'] is True else False

    def fetchBibItems(self, bib):
        return self.queryApi('bibs/{}/{}/items'.format(
            bib['nypl_source'], bib['id']
        )).get('data', [])

    def runProcess(self):
        if self.process == 'daily':
            self.importBibRecords()
        elif self.process == 'complete':
            self.importBibRecords(fullOrPartial=True)
        elif self.process == 'custom':
            self.importBibRecords(startTimestamp=self.ingestPeriod)

        self.saveRecords()
        self.commitChanges()
    
    def parseNYPLDataRow(self, dataRow):
        if self.isResearchBib(dict(dataRow)):
            bibItems = self.fetchBibItems(dict(dataRow))
            nyplRec = NYPLMapping(dataRow, bibItems, self.statics, self.locationCodes)
            nyplRec.applyMapping()
            self.addDCDWToUpdateList(nyplRec)
    
    def importBibRecords(self, fullOrPartial=False, startTimestamp=None):
        nyplBibQuery = 'SELECT * FROM bib'

        if fullOrPartial is False:
            nyplBibQuery += ' WHERE updated_date > '
            if startTimestamp:
                nyplBibQuery += "'{}'".format(startTimestamp)
            else:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
                nyplBibQuery += "'{}'".format(startDateTime.strftime('%Y-%m-%dT%H:%M:%S-%f'))
        
        with self.bibDBConnection.engine.connect() as conn:
            bibResults = conn.execute(nyplBibQuery)
            for bib in bibResults:
                self.parseNYPLDataRow(bib)
