from bs4 import BeautifulSoup
import re
import requests

from managers.parsers.abstractParser import AbstractParser


class SpringerParser(AbstractParser):
    ORDER = 1
    REGEX = r'link.springer.com\/book\/(10\.[0-9]+)(?:\/|\%2F)([0-9\-]+)'
    REDIRECT_REGEX = r'((?:https?:\/\/)?link\.springer\.com\/.+)$'
    STORE_REGEX = r'springer.com\/gp\/book\/(978[0-9]+)$'

    def __init__(self, uri, mediaType, record):
        super().__init__(uri, mediaType, record)

        self.code = None
        self.uriIdentifier = None

    def validateURI(self):
        try:
            match = re.search(self.REGEX, self.uri)

            self.code = match.group(1)
            self.uriIdentifier = match.group(2)

            return True
        except (IndexError, AttributeError):
            if 'springer' in self.uri:
                return self.validateAltLinkFormats()
            
            return False

    def validateAltLinkFormats(self):
        if re.search(self.STORE_REGEX, self.uri):
            self.findOALink()

        redirectMatch = re.search(self.REDIRECT_REGEX, self.uri)

        if redirectMatch:
            self.uri = redirectMatch.group(1)

            redirectHeader = requests.head(self.uri, timeout=5)
            try:
                self.uri = redirectHeader.headers['Location']
                return self.validateURI()
            except KeyError:
                pass
        
        return False

    def findOALink(self):
        storeResp = requests.get(self.uri, timeout=5)

        if storeResp.status_code == 200:
            storePage = BeautifulSoup(storeResp.text, 'html.parser')

            accessLink = storePage.find(class_='openaccess')

            if accessLink: self.uri = accessLink.get('href')

    def createLinks(self):
        s3Root = self.generateS3Root()

        pdfSourceURI = 'https://link.springer.com/content/pdf/{}/{}.pdf'.format(self.code, self.uriIdentifier)
        manifestPath = 'manifests/springer/{}_{}.json'.format(
            self.code.replace('.', '-'), self.uriIdentifier
        )
        manifestURI = '{}{}'.format(s3Root, manifestPath)
        manifestJSON = self.generateManifest(pdfSourceURI, manifestURI)

        ePubSourceURI = 'https://link.springer.com/download/epub/{}/{}.epub'.format(self.code, self.uriIdentifier)
        ePubDownloadPath = 'epubs/springer/{}_{}.epub'.format(
            self.code.replace('.', '-'), self.uriIdentifier
        )
        ePubDownloadURI = '{}{}'.format(s3Root, ePubDownloadPath)

        ePubReadPath = 'epubs/springer/{}_{}/meta-inf/container.xml'.format(
            self.code.replace('.', '-'), self.uriIdentifier
        )
        ePubReadURI = '{}{}'.format(s3Root, ePubReadPath)

        return [
            (ePubReadURI, {'reader': True}, 'application/epub+zip', None, None),
            (ePubDownloadURI, {'download': True}, 'application/epub+xml', None, (ePubDownloadPath, ePubSourceURI)),
            (manifestURI, {'reader': True}, 'application/pdf+json', (manifestPath, manifestJSON), None),
            (pdfSourceURI, {'download': True}, 'application/pdf', None, None),
        ]

    def generateManifest(self, sourceURI, manifestURI):
        return super().generateManifest(sourceURI, manifestURI)

    def generateS3Root(self):
        return super().generateS3Root()
        