import re

from mappings.xml import XMLMapping

class DOABMapping(XMLMapping):
    def __init__(self, source, namespace, statics):
        super(DOABMapping, self).__init__(source, namespace, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('./dc:identifier/text()', '{0}|doab'),
                (
                    [
                        './datacite:alternateIdentifier/text()',
                        './datacite:alternateIdentifier/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'authors': [('./datacite:creator/text()', '{0}|||true')],
            'contributors': [(
                [
                    './datacite:contributor/text()',
                    './datacite:contributor/@type'
                ],
                '{0}||{1}'
            )],
            'title': ('./datacite:title/text()', '{0}'),
            'is_part_of': [('./dc:relation/text()', '{0}||series')],
            'publisher': ('./dc:publisher/text()', '{0}||'),
            'spatial': ('./oapen:placepublication/text()', '{0}'),
            'dates': [
                (
                    [
                        './datacite:date/text()',
                        './datacite:date/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'languages': [('./dc:language/text()', '||{0}')],
            'extent': ('./oapen:pages/text()', '{0} pages'),
            'abstract': ('./dc:description/text()', '{0}'),
            'subjects': [('./datacite:subject/text()', '{0}||')],
            'has_part': [(
                './dc:identifier/text()',
                '1|{0}|doab|text/html|{{"reader": false, "download": false, "catalog": false}}'
            )],
            'rights': [(
                [
                    './oaire:licenseCondition/@uri',
                    './oaire:licenseCondition/text()'
                ],
                'doab|{0}||{1}|'
            )]
        }

    def applyFormatting(self):
        if len(self.record.identifiers) == 0: self.raiseMappingError('Malformed DOAB record')

        self.record.source = 'doab'
        self.record.source_id = list(self.record.identifiers[0].split('|'))[0]

        # Clean up subjects
        self.record.subjects = list(filter(lambda x: x[:3] != 'bic', self.record.subjects))
