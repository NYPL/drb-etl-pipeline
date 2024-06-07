from datetime import datetime, timedelta, timezone
import os
import requests

from .core import CoreProcess
from managers.db import DBManager
from mappings.nypl import NYPLMapping
from sqlalchemy import text


class NYPLProcess(CoreProcess):
    def __init__(self, *args):
        super(NYPLProcess, self).__init__(*args[:4])

        self.ingestLimit = args[4] or None
        self.ingestOffset = args[5] or None

        self.generateEngine()
        self.createSession()
        self.generateAccessToken()

        self.bibDBConnection = DBManager(
            user=os.environ['NYPL_BIB_USER'],
            pswd=os.environ['NYPL_BIB_PSWD'],
            host=os.environ['NYPL_BIB_HOST'],
            port=os.environ['NYPL_BIB_PORT'],
            db=os.environ['NYPL_BIB_NAME']
        )
        self.bibDBConnection.generateEngine()

        self.locationCodes = self.loadLocationCodes()
        self.cceAPI = os.environ['BARDO_CCE_API']

    def loadLocationCodes(self):
        return requests.get(os.environ['NYPL_LOCATIONS_BY_CODE']).json()

    def isPDResearchBib(self, bib):
        currentYear = datetime.today().year
        try:
            pubYear = int(bib['publish_year'])
        except (KeyError, TypeError):
            pubYear = currentYear

        if pubYear > 1965:
            return False
        elif pubYear > currentYear - 95:
            copyrightStatus = self.getCopyrightStatus(bib['var_fields'])
            if copyrightStatus is False: return False

        bibStatus = self.queryApi('bibs/{}/{}/is-research'.format(
            bib['nypl_source'], bib['id']
        ))

        return True if bibStatus.get('isResearch', False) is True else False

    def getCopyrightStatus(self, varFields):
        lccnData = list(filter(lambda x: x.get('marcTag', None) == '010', varFields))
        if not len(lccnData) == 1:
            return False

        lccnNo = lccnData[0]['subfields'][0]['content'].replace('sn', '').strip()

        copyrightURL = '{}/lccn/{}'.format(self.cceAPI, lccnNo)
        copyrightRegResponse = requests.get(copyrightURL)
        if copyrightRegResponse.status_code != 200:
            return False

        copyrightRegData = copyrightRegResponse.json()
        if len(copyrightRegData['data']['results']) > 0:
            return False if len(copyrightRegData['data']['results'][0]['renewals']) > 0 else True

        return False

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
        if self.isPDResearchBib(dict(dataRow)):
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
                nyplBibQuery = text(nyplBibQuery)
            else:
                startDateTime = datetime.now(timezone.utc) - timedelta(hours=24)
                nyplBibQuery += "'{}'".format(startDateTime.strftime('%Y-%m-%dT%H:%M:%S%z'))
                nyplBibQuery = text(nyplBibQuery)

        if self.ingestOffset:
            nyplBibQuery += ' OFFSET {}'.format(self.ingestOffset)

        if self.ingestLimit:
            nyplBibQuery += ' LIMIT {}'.format(self.ingestLimit)

        with self.bibDBConnection.engine.connect() as conn:
            bibResults = conn.execution_options(stream_results=True).execute(nyplBibQuery)
            for bib in bibResults:
                if bib['var_fields'] is None: continue

                self.parseNYPLDataRow(bib)
