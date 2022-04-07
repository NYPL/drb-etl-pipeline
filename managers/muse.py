from bs4 import BeautifulSoup
import json
import os
import requests
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError

from managers import WebpubManifest
from logger import createLog

logger = createLog(__name__)


class MUSEManager:
    MUSE_ROOT = 'https://muse.jhu.edu'

    def __init__(self, record, link, mediaType):
        self.record = record
        self.museID = record.record.source_id
        self.link = link
        self.mediaType = mediaType
        self.museSoup = None

        self.s3Bucket = os.environ['FILE_BUCKET']

        self.pdfDownloadURL = None
        self.epubURL = None
        self.pdfWebpubManifest = None

        self.s3EpubPath = None
        self.s3EpubReadPath = None
        self.s3PDFReadPath = None

    def parseMusePage(self):
        try:
            museHTML = self.loadMusePage()
        except (ReadTimeout, ConnectionError, HTTPError) as err:
            logger.debug('error retrieving page: {}'.format(err))
            raise MUSEError(
                'Unable to load record from link {}'.format(self.link)
            )

        self.museSoup = BeautifulSoup(museHTML, features='lxml')

    def identifyReadableVersions(self):
        # Extract "TOC" section from Project MUSE detail page
        chapterTable = self.museSoup.find(id='available_items_list_wrap')

        # If TOC is not present then there are no manifest-able versions
        if not chapterTable:
            logger.info('Cannot extract PDF/ePub version for MUSE #{}'.format(
                self.museID
            ))
            return None

        # Look for PDF Download Link
        pdfButton = chapterTable.find(alt='Download PDF')
        if pdfButton:
            pdfLink = pdfButton.parent['href']
            self.pdfDownloadURL = '{}{}'.format(self.MUSE_ROOT, pdfLink)
            logger.debug(self.pdfDownloadURL)

        # Look for ePub Link
        epubButton = chapterTable.find(alt='Download EPUB')
        if epubButton:
            epubRelative = epubButton.parent['href']
            self.epubURL = '{}{}'.format(self.MUSE_ROOT, epubRelative)
            logger.debug(self.epubURL)

    def addReadableLinks(self):
        if self.pdfDownloadURL:
            self.record.addHasPartLink(
                self.pdfDownloadURL,
                'application/pdf',
                json.dumps({'download': True, 'reader': False, 'catalog': False})
            )

        if self.epubURL:
            self.s3EpubPath = 'epubs/muse/{}.epub'.format(self.museID)
            self.record.addHasPartLink(
                self.constructS3Link(self.s3EpubPath),
                'application/epub+zip',
                json.dumps({'download': True, 'reader': False, 'catalog': False})
            )

            self.epubReadPath = 'epubs/muse/{}/manifest.json'.format(self.museID)
            self.record.addHasPartLink(
                self.constructS3Link(self.epubReadPath),
                'application/webpub+json',
                json.dumps({'download': False, 'reader': True, 'catalog': False})
            )

        self.constructWebpubManifest()
        if self.pdfWebpubManifest:
            self.s3PDFReadPath = 'manifests/muse/{}.json'.format(self.museID)
            self.record.addHasPartLink(
                self.createManifestInS3(self.s3PDFReadPath),
                'application/webpub+json',
                json.dumps({'reader': True, 'download': False, 'catalog': False})
            )

    def constructWebpubManifest(self):
        pdfManifest = WebpubManifest(self.link, self.mediaType)
        pdfManifest.addMetadata(
            self.record.record, conformsTo=os.environ['WEBPUB_PDF_PROFILE']
        )

        chapterTable = self.museSoup.find(id='available_items_list_wrap')

        if not chapterTable:
            raise MUSEError('Book {} unavailable'.format(self.museID))

        for card in chapterTable.find_all(class_='card_text'):
            titleItem = card.find('li', class_='title')
            pdfItem = card.find(alt='Download PDF')

            if not titleItem.span.a:
                pdfManifest.addSection(titleItem.span.string, '')
                continue

            if card.parent.get('style') != 'margin-left:30px;':
                pdfManifest.closeSection()

            if pdfItem:
                #skipCover indicates whether to skip the intersitital cover page by adding a query parameter
                skipCover = False
                if skipCover == False:
                    pdfManifest.addChapter(
                        '{}{}'.format(
                            self.MUSE_ROOT, pdfItem.parent.get('href')
                        ),
                        titleItem.span.a.string,
                    )
                if skipCover == True:
                    queryParam = '?start=2'
                    pdfManifest.addChapter(
                        '{}{}{}'.format(
                            self.MUSE_ROOT, pdfItem.parent.get('href'), queryParam
                        ),
                        titleItem.span.a.string,
                    )
            skipCover = True

        pdfManifest.closeSection()

        if len(pdfManifest.readingOrder) > 0:
            self.pdfWebpubManifest = pdfManifest

    def loadMusePage(self):
        museResponse = requests.get(
            self.link, timeout=15, headers={'User-agent': 'Mozilla/5.0'}
        )

        museResponse.raise_for_status()

        return museResponse.text

    def constructS3Link(self, bucketLocation):
        return 'https://{}.s3.amazonaws.com/{}'.format(
            self.s3Bucket, bucketLocation
        )

    def createManifestInS3(self, bucketLocation):
        s3URL = self.constructS3Link(bucketLocation)

        self.pdfWebpubManifest.links.append(
            {'href': s3URL, 'type': 'application/webpub+json', 'rel': 'self'}
        )

        return s3URL


class MUSEError(Exception):
    def __init__(self, message):
        self.message = message
