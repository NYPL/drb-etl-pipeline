from abc import ABC, abstractmethod
import os
import re

from managers.pdfManifest import PDFManifest

class AbstractParser(ABC):
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
        manifest = PDFManifest(sourceURI, 'application/pdf')

        manifest.addMetadata(self.record)

        manifest.addChapter(sourceURI, self.record.title, None)

        manifest.links['self'] = {'href': manifestURI, 'type': 'application/pdf+json'}

        return manifest.toJson()

    @abstractmethod
    def generateS3Root(self):
        s3Bucket = os.environ['FILE_BUCKET']
        return 'https://{}.s3.amazonaws.com/'.format(s3Bucket)
