import csv
from datetime import datetime
import gzip
import os
import requests

from .core import CoreProcess
from mappings.hathitrust import HathiMapping
from logger import createLog

logger = createLog(__name__)

class HathiTrustProcess(CoreProcess):
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']

    def __init__(self, *args):
        super(HathiTrustProcess, self).__init__(*args[:4])
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
        logger.info('Running standard {} Hathi ingest'.format(
            'complete' if fullOrPartial else 'daily'
        ))
        self.importFromHathiTrustDataFile(fullDump=fullOrPartial)

    def importFromSpecificFile(self, filePath):
        logger.info('Running custom local ingest from {}'.format(filePath))
        try:
            hathiFile = open(filePath, newline='')
        except FileNotFoundError:
            raise IOError('Unable to open local CSV file')

        hathiReader = csv.reader(hathiFile, delimiter='\t')
        self.readHathiFile(hathiReader)

    def parseHathiDataRow(self, dataRow):
        hathiRec = HathiMapping(dataRow, self.statics)
        hathiRec.applyMapping()
        self.addDCDWToUpdateList(hathiRec)
    
    def importFromHathiTrustDataFile(self, fullDump=False):
        fileList = requests.get(os.environ['HATHI_DATAFILES'])
        if fileList.status_code != 200:
            logger.error('Unable to load Hathi datafile with status'.format(fileList.status_code))
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
                logger.debug('Loading datafile {}'.format(hathiFile['filename']))

                with open('/tmp/tmp_hathi.txt.gz', 'wb') as hathiTSV:
                    hathiReq = requests.get(hathiFile['url'])
                    hathiTSV.write(hathiReq.content)
                break

        logger.debug('Writing Hathi TSV to /tmp/tmp_hathi.txt.gz')
        with gzip.open('/tmp/tmp_hathi.txt.gz', 'rt') as unzipTSV:
            hathiTSV = csv.reader(unzipTSV, delimiter='\t')
            self.readHathiFile(hathiTSV)

    def readHathiFile(self, hathiTSV):
        while True:
            try:
                row = next(hathiTSV)
            except csv.Error:
                logger.warning('Unable to read TSV row')
                continue
            except StopIteration:
                logger.debug('Reached end of TSV file, breaking')
                break

            if row is not None and row[2] not in self.HATHI_RIGHTS_SKIPS:
                self.parseHathiDataRow(row)
