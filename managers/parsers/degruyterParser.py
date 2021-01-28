import re
import requests

from managers.parsers.abstractParser import AbstractParser
from managers.pdfManifest import PDFManifest


class DeGruyterParser(AbstractParser):
    ORDER = 5
    REGEX = r'www\.degruyter\.com\/.+\/[0-9]+'

    def __init__(self, uri, mediaType, record):
        super().__init__(uri, mediaType, record)

        self.uriIdentifier = None

    def validateURI(self):
        return True if re.search(self.REGEX, self.uri) else False

    def createLinks(self):
        s3Root = self.generateS3Root()

        isbnMatch = re.search(r'(978[0-9]+)', self.uri)

        if isbnMatch is not None:
            degISBN = isbnMatch.group(1)
            isbnPath = '/'.join([degISBN] * 3)
            self.uri = 'https://www.degruyter.com/view/books/{}.xml'.format(isbnPath)

            uriStatus, uriHeaders = DeGruyterParser.makeHeadQuery(self.uri)

            if uriStatus == 301:
                self.uri = uriHeaders['Location']

        idMatch = re.search(r'\/title\/([0-9]+)(?:$|\?)', self.uri)

        if idMatch:
            self.uriIdentifier = idMatch.group(1)

            pdfLink = self.generatePDFLinks(s3Root)

            ePubLinks = self.generateEpubLinks(s3Root)

            return list(filter(None, [*pdfLink, *ePubLinks]))

        return super().createLinks()
        
    def generateEpubLinks(self, s3Root):
        ePubSourceURI = 'https://www.degruyter.com/downloadepub/title/{}'.format(self.uriIdentifier)

        ePubHeadStatus, _ = DeGruyterParser.makeHeadQuery(ePubSourceURI)
        
        if ePubHeadStatus != 200:
            return [None]

        ePubDownloadPath = 'epubs/degruyter/{}.epub'.format(self.uriIdentifier)
        ePubDownloadURI = '{}{}'.format(s3Root, ePubDownloadPath)

        ePubReadPath = 'epubs/degruyter/{}/meta-inf/container.xml'.format(self.uriIdentifier)
        ePubReadURI = '{}{}'.format(s3Root, ePubReadPath)

        return [
            (ePubReadURI, {'reader': True}, 'application/epub+xml', None, None),
            (ePubDownloadURI, {'download': True}, 'application/epub+zip', None, (ePubDownloadPath, ePubSourceURI)),
        ]

    def generatePDFLinks(self, s3Root):
        pdfSourceURI = 'https://www.degruyter.com/downloadpdf/title/{}'.format(self.uriIdentifier)
        manifestPath = 'manifests/degruyter/{}.json'.format(self.uriIdentifier)
        manifestURI = '{}{}'.format(s3Root, manifestPath)
        manifestJSON = self.generateManifest(pdfSourceURI, manifestURI)

        return [
            (manifestURI, {'reader': True}, 'application/pdf+json', (manifestPath, manifestJSON), None),
            (pdfSourceURI, {'download': True}, 'application/pdf', None, None)
        ]

    def generateManifest(self, sourceURI, manifestURI):
        return super().generateManifest(sourceURI, manifestURI)

    def generateS3Root(self):
        return super().generateS3Root()

    @staticmethod
    def makeHeadQuery(uri):
        headResp = requests.head(uri, timeout=5, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5)'})

        return (headResp.status_code, headResp.headers)
