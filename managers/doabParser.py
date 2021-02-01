import inspect
import json
import requests
from requests.exceptions import ConnectionError, InvalidURL, MissingSchema, ReadTimeout 

import managers.parsers as parsers


class DOABLinkManager:
    def __init__(self, record):
        self.record = record
        self.manifests = []
        self.ePubLinks = []
        self.linksProcessed = []

        self.loadParsers()

    def loadParsers(self):
        parserList = inspect.getmembers(parsers, inspect.isclass)

        self.parsers = [None] * len(parserList)

        for parser in parserList:
            _, parserClass = parser
            self.parsers[parserClass.ORDER - 1] = parserClass

    def selectParser(self, uri, mediaType):
        rootURI, rootMediaType = self.findFinalURI(uri, mediaType)

        for parserClass in self.parsers:
            parser = parserClass(rootURI, rootMediaType, self.record)

            if parser.validateURI() is True:
                return parser

    def parseLinks(self):
        parsedLinks = []
        for part in self.record.has_part:
            partNo, partURI, partSource, partType, partFlags = list(part.split('|'))

            try:
                parser = self.selectParser(partURI, partType)
            except LinkError:
                print('Unable to parse {}'.format(partURI))
                continue

            if parser.uri in self.linksProcessed:
                continue

            self.linksProcessed.append(parser.uri)

            for parserLink in parser.createLinks():
                parserURI, parserFlags, parserType, manifest, ePubFile = parserLink

                if parserFlags:
                    partFlagDict = json.loads(partFlags)
                    partFlagDict.update(parserFlags)
                    partFlags = json.dumps(partFlagDict)

                parsedLinks.append('|'.join([partNo, parserURI, partSource, parserType, partFlags]))

                if manifest:
                    self.manifests.append(manifest)

                if ePubFile:
                    self.ePubLinks.append(ePubFile)

        self.record.has_part = parsedLinks
    
    @staticmethod
    def findFinalURI(uri, mediaType):
        try:
            uriHeader = requests.head(uri, allow_redirects=False, verify=False, timeout=15)
            headers = uriHeader.headers
        except(MissingSchema, ConnectionError, InvalidURL, ReadTimeout):
            raise LinkError('Invalid has_part URI')

        try:
            contentHeader = headers['Content-Type']
            mediaType = list(contentHeader.split(';'))[0].strip()
        except KeyError:
            pass

        if uriHeader.status_code in [301, 302, 307, 308]\
            and headers.get('Content-Type', None) not in ['application/pdf', 'application/epub+zip']:
            redirectURI = headers['Location']
            return DOABLinkManager.findFinalURI(redirectURI, mediaType)
        
        return (uri, mediaType)


class LinkError(Exception):
    def __init__(self, message):
        self.message = message
