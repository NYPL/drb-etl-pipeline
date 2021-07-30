from abc import ABC, abstractmethod
import os
import re

from managers.webpubManifest import WebpubManifest


class AbstractParser(ABC):
    TIMEOUT = 15

    @abstractmethod
    def __init__(self, uri, mediaType, record):
        self.uri = uri
        self.mediaType = mediaType
        self.record = record

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        if not re.match(r'https?:\/\/', value):
            self._uri = 'http://{}'.format(value)
        else:
            self._uri = value

    @abstractmethod
    def validateURI(self):
        return True

    @abstractmethod
    def createLinks(self):
        return [(self.uri, None, self.mediaType, None, None)]

    @abstractmethod
    def generateManifest(self, sourceURI, manifestURI):
        manifest = WebpubManifest(sourceURI, 'application/pdf')

        manifest.addMetadata(
            self.record, conformsTo=os.environ['WEBPUB_PDF_PROFILE']
        )

        manifest.addChapter(sourceURI, self.record.title)

        manifest.links.append({
            'rel': 'self',
            'href': manifestURI,
            'type': 'application/webpub+json'
        })

        return manifest.toJson()

    @abstractmethod
    def generateS3Root(self):
        s3Bucket = os.environ['FILE_BUCKET']
        return 'https://{}.s3.amazonaws.com/'.format(s3Bucket)
