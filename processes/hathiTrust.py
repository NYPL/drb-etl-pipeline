import csv
from datetime import datetime
import gzip
import os
import requests
import sys

from .core import CoreProcess
from mappings.hathitrust import HathiMapping
from model import Record


class HathiTrustProcess(CoreProcess):
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']

    def __init__(self, process, customFile, ingestPeriod):
        super(HathiTrustProcess, self).__init__(process, customFile, ingestPeriod)
        self.generateEngine()
        self.createSession()

    def runProcess(self):
        if self.process == 'daily':
            self.importRemoteRecords()
        elif self.process == 'complete':
            self.importRemoteRecords(fullOrPartial=True)
        elif self.process == 'custom':
            self.importFromSpecificFile(self.customFile)

        self.saveRecords()
        self.commitChanges()
    
    def importRemoteRecords(self, fullOrPartial=False):
        self.importFromHathiTrustDataFile(fullDump=fullOrPartial)

    def importFromSpecificFile(self, filePath):
        try:
            hathiFile = open(filePath, newline='')
        except FileNotFoundError:
            raise IOError('Unable to open local CSV file')

        hathiReader = csv.reader(hathiFile)

        for row in hathiReader:
            if row[2] not in self.HATHI_RIGHTS_SKIPS and row[0] != 'htid':
                self.parseHathiDataRow(row)

    def parseHathiDataRow(self, dataRow):
        hathiRec = HathiMapping(dataRow, self.statics)
        hathiRec.applyMapping()
        self.addDCDWToUpdateList(hathiRec)
    
    def importFromHathiTrustDataFile(self, fullDump=False):
        fileList = requests.get(os.environ['HATHI_DATAFILES'])
        if fileList.status_code != 200:
            raise IOError('Unable to load data files')

        fileJSON = fileList.json()

        fileJSON.sort(
            key=lambda x: datetime.strptime(
                x['created'],
                '%Y-%m-%dT%H:%M:%S%z'
            ).timestamp(),
            reverse=True
        )

        for hathiFile in fileJSON:
            if hathiFile['full'] == fullDump:
                with open('/tmp/tmp_hathi.txt.gz', 'wb') as hathiTSV:
                    hathiReq = requests.get(hathiFile['url'])
                    hathiTSV.write(hathiReq.content)
                break

        with gzip.open('/tmp/tmp_hathi.txt.gz', 'rt') as unzipTSV:
            hathiTSV = csv.reader(unzipTSV, delimiter='\t')
            for row in hathiTSV:
                if row[2] not in self.HATHI_RIGHTS_SKIPS:
                    self.parseHathiDataRow(row)
