from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
from io import BytesIO, StringIO
import json
import os
from pymarc import MARCReader
import requests
from requests.exceptions import ReadTimeout, HTTPError

from .core import CoreProcess
from mappings.muse import MUSEMapping
from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)


class MUSEProcess(CoreProcess):
    MUSE_ROOT_URL = 'https://muse.jhu.edu'

    def __init__(self, *args):
        super(MUSEProcess, self).__init__(*args[:4])

        self.generateEngine()
        self.createSession()

        self.createS3Client()
        self.s3Bucket = os.environ['FILE_BUCKET']

    def runProcess(self):
        if self.process == 'daily':
            self.importMARCRecords()
        elif self.process == 'complete':
            self.importMARCRecords(full=True)
        elif self.process == 'custom':
            self.importMARCRecords(startTimestamp=self.ingestPeriod)

        self.saveRecords()
        self.commitChanges()
    
    def parseMuseRecord(self, marcRec):
        museRec = MUSEMapping(marcRec)
        museRec.applyMapping()

        # Use the available source link to create a PDF manifest file and store in S3
        _, museLink, _, museType, _ = list(museRec.record.has_part[0].split('|'))
        webpubManifest = self.constructPDFManifest(museLink, museType, museRec.record)

        s3URL = self.createManifestInS3(webpubManifest, museRec.record.source_id)
        museRec.addHasPartLink(
            s3URL, 'application/webpub+json',
            json.dumps({'reader': True, 'download': False, 'catalog': False})
        )
        self.addDCDWToUpdateList(museRec)
    
    def importMARCRecords(self, full=False, startTimestamp=None):
        self.downloadRecordUpdates()

        museFile = self.downloadMARCRecords()

        startDateTime = None
        if full is False:
            if not startTimestamp:
                startDateTime = datetime.utcnow() - timedelta(hours=24)
            else:
                startDateTime = datetime.strptime(startTimestamp, '%Y-%m-%d')

        marcReader = MARCReader(museFile)

        for record in marcReader:
            if startDateTime and self.recordToBeUpdated(record, startDateTime) is False:
                continue

            try:
                self.parseMuseRecord(record)
            except MUSEError as e:
                logger.warning('Unable to parse MUSE record')
                logger.debug(e)

    def downloadMARCRecords(self):
        marcURL = os.environ['MUSE_MARC_URL']

        try:
            museResponse = requests.get(marcURL, stream=True, timeout=30)
            museResponse.raise_for_status()
        except(ReadTimeout, HTTPError) as e:
            logger.error('Unable to load MUSE MARC records')
            logger.debug(e)
            raise Exception('Unable to load Project MUSE MARC file')

        content = bytes()
        for chunk in museResponse.iter_content(1024 * 250):
            content += chunk

        return BytesIO(content)

    def downloadRecordUpdates(self):
        marcCSVURL = os.environ['MUSE_CSV_URL']

        try:
            csvResponse = requests.get(marcCSVURL, stream=True, timeout=30)
            csvResponse.raise_for_status()
        except(ReadTimeout, HTTPError) as e:
            logger.error('Unable to load MUSE CSV records')
            logger.debug(e)
            raise Exception('Unable to load Project MUSE CSV file')

        csvReader = csv.reader(
            csvResponse.iter_lines(decode_unicode=True),
            skipinitialspace=True,
        )

        for _ in range(4): next(csvReader, None) # Skip 4 header rows

        self.updateDates = {}
        for row in csvReader:
            try:
                self.updateDates[row[7]] = datetime.strptime(row[10], '%Y-%m-%d')
            except (IndexError, ValueError):
                logger.warning('Unable to parse MUSE')
                logger.debug(row)

    def recordToBeUpdated(self, record, startDate):
        recordURL = record.get_fields('856')[0]['u']
        return self.updateDates.get(recordURL[:-1], datetime(1970, 1, 1)) >= startDate

    def constructPDFManifest(self, museLink, museType, museRecord):
        try:
            museHTML = self.loadMusePage(museLink)
        except Exception as e:
            raise MUSEError('Unable to load record from link {}'.format(museLink))

        pdfManifest = WebpubManifest(museLink, museType)
        pdfManifest.addMetadata(museRecord)

        museSoup = BeautifulSoup(museHTML, features='lxml')

        chapterTable = museSoup.find(id='available_items_list_wrap')

        if not chapterTable:
            raise MUSEError('Book {} unavailable'.format(museRecord.source_id))

        for card in chapterTable.find_all(class_='card_text'):
            titleItem = card.find('li', class_='title')

            if not titleItem:
                continue
            elif not titleItem.span.a:
                pdfManifest.addSection(titleItem.span.string, '')
                continue
            else:
                if card.parent.get('style') != 'margin-left:30px;':
                    pdfManifest.closeSection()

                pdfManifest.addChapter(
                    '{}{}/pdf'.format(self.MUSE_ROOT_URL, titleItem.span.a.get('href')),
                    titleItem.span.a.string,
                )
        
        pdfManifest.closeSection()
        
        return pdfManifest
    
    def loadMusePage(self, museLink):
        museResponse = requests.get(museLink, timeout=15, headers={'User-agent': 'Mozilla/5.0'})

        if museResponse.status_code == 200:
            return museResponse.text

        raise Exception('Unable to load HTML page from Project MUSE')

    def createManifestInS3(self, webpubManifest, museID):
        bucketLocation = 'manifests/muse/{}.json'.format(museID)
        s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, bucketLocation)

        webpubManifest.links.append({'href': s3URL, 'type': 'application/webpub+json', 'rel': 'self'})

        self.putObjectInBucket(webpubManifest.toJson().encode('utf-8'), bucketLocation, self.s3Bucket)

        return s3URL


class MUSEError(Exception):
    def __init__(self, message):
        self.message = message
