import json
import os


class WebpubManifest:
    def __init__(self, source, sourceType):
        self.metadata = {'@type': 'https://schema.org/Book'}
        self.links = [{'href': source, 'type': sourceType, 'rel': 'alternate'}]
        self.readingOrder = []
        self.resources = set()
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
    def addChapter(self, link, title, subsections=None):
        component = {'href': link, 'title': title}
        tocEntry = component.copy()

        if subsections and isinstance(subsections, list):
            tocEntry['children'] = subsections

        if self.openSection:
            self.openSection['children'].append(tocEntry)
        else:
            self.tableOfContents.append(tocEntry)

        self.addReadingOrder(component)
        self.addResource(component['href'])

    def addReadingOrder(self, component):
        component['type'] = 'application/pdf'

        self.readingOrder.append(component)

    def addResource(self, href):
        rootHref, *_ = href.split('#')

        self.resources.add(rootHref)

    def toDict(self):
        return {
            'context': 'https://{}-s3.amazonaws.com/manifests/context.jsonld'.format(os.environ['FILE_BUCKET']),
            'metadata': self.metadata,
            'links': self.links,
            'readingOrder': self.readingOrder,
            'resources': [{'href': res, 'type': 'application/pdf'} for res in self.resources],
            'toc': self.tableOfContents
        }

    def toJson(self):
        return json.dumps(self.toDict())
