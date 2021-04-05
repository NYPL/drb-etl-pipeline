import json
import os
import re


class WebpubManifest:
    def __init__(self, source, sourceType):
        self.metadata = {'@type': 'https://schema.org/Book'}
        self.links = {
            'self': {},
            'alternate': [{'href': source, 'type': sourceType}]
        }
        self.components = []
        self.tableOfContents = []

        self.openSection = None

    # TODO validate kwargs against schema.org/Book
    def addMetadata(self, dcdwRecord):
        self.metadata['title'] = dcdwRecord.title

        if len(dcdwRecord.authors) > 0:
            self.metadata['author'] = list(dcdwRecord.authors[0].split('|'))[0]

        isbns = list(filter(lambda x: x[-4:] == 'isbn', dcdwRecord.identifiers))
        if len(isbns) > 0:
            self.metadata['identifier'] = 'urn:isbn:{}'.format(isbns[0][:-5])

    def addSection(self, sectionTitle, sectionURL):
        if self.openSection:
            self.tableOfContents.append(self.openSection)

        self.openSection = {
            'href': sectionURL,
            'title': sectionTitle,
            'children': []
        }

    def closeSection(self):
        if self.openSection:
            self.tableOfContents.append(self.openSection)
        
        self.openSection = None

    # TODO Make it possible to add subsections iteratively
    def addChapter(self, link, title, pageRange, subsections=None):
        newChapter = PDFChapter(link, title, pageRange)
        newChapter.parsePageRange()

        tocEntry = {
            'href': link, 'title': title, 'pages': pageRange
        }

        if subsections and isinstance(subsections, list):
            tocEntry['children'] = subsections

        if self.openSection:
            self.openSection['children'].append(tocEntry)
        else:
            self.tableOfContents.append(tocEntry)

        self.components.append(newChapter)

    def toDict(self):
        return {
            'context': 'https://{}-s3.amazonaws.com/manifests/context.jsonld'.format(os.environ['FILE_BUCKET']),
            'metadata': self.metadata,
            'links': self.links,
            'readingOrder': [c.toDict() for c in self.components],
            'resources': [c.toDict(resource=True) for c in self.components],
            'toc': self.tableOfContents
        }

    def toJson(self):
        return json.dumps(self.toDict())


class PDFChapter:
    ROMAN_NUMERALS = {'i': 1, 'v': 5, 'x': 10, 'l': 50, 'c': 100, 'm': 1000}
    def __init__(self, link, title, pageRange):
        self.link = link
        self.title = title
        self.pageRange = pageRange
        self.startPage = None
        self.endPage = None

        self.type = 'application/pdf'

    def parsePageRange(self):
        if not self.pageRange: return None

        rangeMatch = re.search(r'([\w]+)\-([\w]+)', self.pageRange)

        if rangeMatch:
            self.startPage = self.parseRangeValue(rangeMatch.group(1))
            self.endPage = self.parseRangeValue(rangeMatch.group(2))

    @classmethod
    def parseRangeValue(cls, rangeValue):
        try:
            return int(rangeValue)
        except ValueError:
            return cls.translateRomanNumeral(rangeValue)

    @classmethod
    def translateRomanNumeral(cls, rangeValue):
        rangeLower = rangeValue.lower()

        if not re.search(r'^[ivxlcm]+$', rangeLower): return None

        num = 0
        pos = 0
        charVal = cls.ROMAN_NUMERALS[rangeLower[pos]]
        while pos < len(rangeLower):
            pos += 1

            try:
                nextCharVal = cls.ROMAN_NUMERALS[rangeLower[pos]]
            except IndexError:
                num += charVal
                break

            if charVal < nextCharVal:
                charVal = charVal * -1

            num += charVal

            charVal = nextCharVal
                
        return num

    def toDict(self, resource=False):
        componentEntry = {
            'href': self.link, 'title': self.title
        }

        if self.startPage:
            componentEntry['pageStart'] = self.startPage

        if self.endPage:
            componentEntry['pageEnd'] = self.endPage

        return componentEntry
