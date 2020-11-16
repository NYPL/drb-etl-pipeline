import json
import re

from mappings.xml import XMLMapping

class ClassifyMapping(XMLMapping):
    def __init__(self, source, namespace, statics, sourceID):
        super(ClassifyMapping, self).__init__(source, namespace, statics)
        self.mapping = self.createMapping()
        self.sourceID, self.sourceIDType = sourceID
    
    def createMapping(self):
        return {
            'title': ('//oclc:work/@title', '{0}'),
            'identifiers': [
                ('//oclc:work/@owi', '{0}|owi'),
                ('//oclc:work/text()', '{0}|oclc'),
                ('//oclc:editions/oclc:edition/@oclc', '{0}|oclc')
            ],
            'authors': [(
                [
                    '//oclc:authors/oclc:author/text()',
                    '//oclc:authors/oclc:author/@lc',
                    '//oclc:authors/oclc:author/@viaf'
                ],
                '{0}|{2}|{1}|true')
            ],
            'subjects': [(
                [
                    '//oclc:heading/text()',
                    '//oclc:heading/@ident',
                    '//oclc:heading/@src'
                ],
                '{0}|{1}|{2}')
            ]
        }

    def applyFormatting(self):
        self.record.source = 'oclcClassify'
        self.record.source_id = self.record.identifiers[0]

        self.record.identifiers.append('{}|{}'.format(self.sourceID, self.sourceIDType))

        self.record.frbr_status = 'complete'
