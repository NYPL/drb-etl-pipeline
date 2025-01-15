import re

from mappings.xml import XMLMapping

class CLACSOMapping(XMLMapping):
    def __init__(self, source, namespace, constants):
        super(CLACSOMapping, self).__init__(source, namespace, constants)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('./dc:title/text()', '{0}'),
            'authors': [('./dc:creator/text()', '{0}|||true')],
            'abstract': ('./dc:description/text()', '{0}'),
            'dates': [
                (
                    [
                        './dc:date/text()',
                        './dc:date/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'identifiers': [
                ('./dc:identifier/text()', '{0}|clacso'),
                (
                    [
                        './dc:alternateIdentifier/text()',
                        './datacite:alternateIdentifier/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'spatial': ('edition_location', '{0}'),
            'has_part': [(
                './dc:identifier/text()',
                '1|{0}|doab|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}'
            )], 
        }

    def applyFormatting(self):
        self.record.source = 'clacso'
        self.record.source_id = f'{self.record.source}'
