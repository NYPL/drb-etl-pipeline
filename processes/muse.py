from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from io import BytesIO
import json
import os
from pymarc import MARCReader
import requests

from .core import CoreProcess
from mappings.muse import MUSEMapping
from managers import PDFManifest


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
            self.importMARCRecords(fullOrPartial=True)
        elif self.process == 'custom':
            self.importMARCRecords(startTimestamp=self.ingestPeriod)

        self.saveRecords()
        self.commitChanges()
    
    def parseMuseRecord(self, marcRec):
        museRec = MUSEMapping(marcRec)
        museRec.applyMapping()

        # Use the available source link to create a PDF manifest file and store in S3
        _, museLink, _, museType, _ = list(museRec.record.has_part[0].split('|'))
        pdfManifest = self.constructPDFManifest(museLink, museType, museRec.record)

        s3URL = self.createManifestInS3(pdfManifest, museRec.record.source_id)
        museRec.addHasPartLink(
            s3URL, 'application/pdf+json',
            json.dumps({'reader': True, 'download': False, 'catalog': False})
        )
        self.addDCDWToUpdateList(museRec)
    
    def importMARCRecords(self, fullOrPartial=False, startTimestamp=None):
        museFile = self.downloadMARCRecords()

        marcReader = MARCReader(museFile)

        for record in marcReader:
            try:
                self.parseMuseRecord(record)
            except MUSEError as e:
                print('ERROR', e)
                pass

    def downloadMARCRecords(self):
        marcURL = os.environ['MUSE_MARC_URL']

        museResponse = requests.get(marcURL, stream=True, timeout=30)

        if museResponse.status_code == 200:
            content = bytes()
            for chunk in museResponse.iter_content(1024):
                content += chunk

            return BytesIO(content)

        raise Exception('Unable to load Project MUSE MARC file')

    def constructPDFManifest(self, museLink, museType, museRecord):
        try:
            museHTML = self.loadMusePage(museLink)
        except Exception as e:
            return None

        pdfManifest = PDFManifest(museLink, museType)
        pdfManifest.addMetadata(museRecord)

        museSoup = BeautifulSoup(museHTML, features='lxml')

        chapterTable = museSoup.find(id='available_items_list_wrap')

        if not chapterTable: raise MUSEError('Book {} unavailable'.format(museRecord.source_id))

        for card in chapterTable.find_all(class_='card_text'):
            titleItem = card.find('li', class_='title')
            pageItem = card.find('li', class_='pg')

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
                    pageItem.string if pageItem else None
                )
        
        pdfManifest.closeSection()
        
        return pdfManifest
    
    def loadMusePage(self, museLink):
        museResponse = requests.get(museLink, timeout=15, headers={'User-agent': 'Mozilla/5.0'})

        if museResponse.status_code == 200:
            return museResponse.text

        raise Exception('Unable to load HTML page from Project MUSE')

    def createManifestInS3(self, pdfManifest, museID):
        bucketLocation = 'manifests/muse/{}.json'.format(museID)
        s3URL = 'https://{}.s3.amazonaws.com/{}'.format(self.s3Bucket, bucketLocation)

        pdfManifest.links['self'] = {'href': s3URL, 'type': 'application/pdf+json'}

        self.putObjectInBucket(pdfManifest.toJson().encode('utf-8'), bucketLocation, self.s3Bucket)

        return s3URL


class MUSEError(Exception):
    def __init__(self, message):
        self.message = message
