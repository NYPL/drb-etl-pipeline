import csv
from datetime import datetime
from io import BytesIO
import gzip
import os
import requests
from requests.exceptions import ReadTimeout, HTTPError

from ..core import CoreProcess
from mappings.hathitrust import HathiMapping
from logger import createLog

logger = createLog(__name__)

class HathiTrustProcess(CoreProcess):
    HATHI_RIGHTS_SKIPS = ['ic', 'icus', 'ic-world', 'und']

    def __init__(self, *args):
        super(HathiTrustProcess, self).__init__(*args[:4], batchSize=1000)

        self.ingest_limit = int(args[4]) if args[4] else None

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

        logger.info(f'Ingested {len(self.records)} Hathi Trust records')

    def importRemoteRecords(self, fullOrPartial=False):
        self.importFromHathiTrustDataFile(fullDump=fullOrPartial)

    def importFromSpecificFile(self, filePath):
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
        try:
            fileList = requests.get(os.environ['HATHI_DATAFILES'], timeout=15)
            fileList.raise_for_status()
        except (ReadTimeout, HTTPError):
            raise IOError('Unable to load data files')

        fileJSON = fileList.json()

        fileJSON.sort(
            key=lambda x: datetime.strptime(
                x['created'],
                self.returnHathiDateFormat(x['created'])
            ).timestamp(),
            reverse=True
        )

        for hathiFile in fileJSON:
            if hathiFile['full'] == fullDump:
                self.importFromHathiFile(hathiFile['url'])
                break

    @staticmethod
    def returnHathiDateFormat(strDate):
        if 'T' in strDate and '-' in strDate:
            return '%Y-%m-%dT%H:%M:%S%z'
        elif 'T' in strDate:
            return '%Y-%m-%dT%H:%M:%S'
        else:
            return '%Y-%m-%d %H:%M:%S %z'

    def importFromHathiFile(self, hathiURL):
        try:
            hathiResp = requests.get(hathiURL, stream=True, timeout=30)
            hathiResp.raise_for_status()
        except (ReadTimeout, HTTPError) as e:
            logger.error('Unable to read hathifile url {}'.format(hathiURL))
            logger.debug(e)
            return None

        with gzip.open(BytesIO(hathiResp.content), mode='rt') as hathiGzip:
            hathiTSV = csv.reader(hathiGzip, delimiter='\t')
            self.readHathiFile(hathiTSV)

    def readHathiFile(self, hathiTSV):
        processed_record_count = 0

        while True:
            if self.ingest_limit and processed_record_count >= self.ingest_limit:
                break

            try:
                row = next(hathiTSV)
                logger.info('Reading row')
            except csv.Error as e:
                logger.warning('Unable to read TSV row')
                logger.debug(e)
                continue
            except StopIteration:
                logger.info('Reached end of TSV file')
                break

            if row is not None and row[2] not in self.HATHI_RIGHTS_SKIPS:
                self.parseHathiDataRow(row)
                processed_record_count += 1
