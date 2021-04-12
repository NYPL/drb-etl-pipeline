import re

from mappings.xml import XMLMapping

class DOABMapping(XMLMapping):
    DOI_REGEX = r'doabooks.org\/handle\/([0-9]+\.[0-9]+\.[0-9]+\/[0-9]+)'
    def __init__(self, source, namespace, statics):
        super(DOABMapping, self).__init__(source, namespace, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('./dc:identifier/text()', '{0}|doab'),
                ('./datacite:identifier/text()', '{0}|doab'),
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
                '{0}|||{1}'
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
            'rights': [
                (
                    [
                        './oaire:licenseCondition/@uri',
                        './oaire:licenseCondition/text()'
                    ],
                    'doab|{0}||{1}|'
                ),
                (
                    [
                        './datacite:rights/@uri',
                        './datacite:rights/text()'
                    ],
                    'doab|{0}||{1}|'
                )
            ]
        }

    def applyFormatting(self):
        # Set Identifiers
        self.record.source = 'doab'
        self.record.identifiers = self.parseIdentifiers()

        # Clean up subjects
        self.record.subjects = list(filter(lambda x: x[:3] != 'bic', self.record.subjects))

        # Clean up rights statements
        self.record.rights = self.parseRights()

        # Clean up links
        self.record.has_part = self.parseLinks()

        if self.record.source_id is None or len(self.record.identifiers) < 1:
            self.raiseMappingError('Malformed DOAB record')

    def parseIdentifiers(self):
        outIDs = []

        for iden in self.record.identifiers:
            value, auth = iden.split('|')

            if value[:4] == 'http':
                doabDOIGroup = re.search(self.DOI_REGEX, value)

                if doabDOIGroup:
                    value = doabDOIGroup.group(1)
                    self.record.source_id = value
                else:
                    continue

            outIDs.append('{}|{}'.format(value, auth.lower()))

        return outIDs

    def parseRights(self):
        outRights = []

        for rightsObj in self.record.rights:
            rightsData = [d.strip() for d in list(rightsObj.split('|'))]

            if rightsData[1] == '': continue

            outRights.append('|'.join(rightsData))

        return outRights

    def parseLinks(self):
        outLinks = []
        
        for link in self.record.has_part:
            _, uri, *_ = link.split('|')

            if uri[:4] != 'http': continue

            outLinks.append(link)
        
        return outLinks
