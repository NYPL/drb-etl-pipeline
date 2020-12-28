import json
import re

from mappings.xml import XMLMapping

class CatalogMapping(XMLMapping):
    def __init__(self, source, namespace, statics):
        super(CatalogMapping, self).__init__(source, namespace, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('//oclc:datafield[@tag=\'245\']/oclc:subfield[@code=\'a\' or @code=\'b\']/text()', '{0} {1}'),
            'alternative': [
                ('//oclc:datafield[@tag=\'210\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'222\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'242\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'246\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'247\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            ],
            'authors': [
                ([
                    '//oclc:datafield[@tag=\'100\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'100\']/oclc:subfield[@code=\'d\']/text()',
                ], '{0} ({1})||true'),
                ([
                    '//oclc:datafield[@tag=\'110\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'110\']/oclc:subfield[@code=\'b\']/text()',
                ], '{0} {1}||true')
            ],
            'publisher': ('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'b\']/text()', '{0}||'),
            'identifiers': [
                ('//oclc:controlfield[@tag=\'001\']/text()', '{0}|oclc'),
                ('//oclc:datafield[@tag=\'010\']/oclc:subfield[@code=\'a\']/text()', '{0}|lccn'),
                ('//oclc:datafield[@tag=\'020\']/oclc:subfield[@code=\'a\']/text()', '{0}|isbn'),
                ('//oclc:datafield[@tag=\'022\']/oclc:subfield[@code=\'a\']/text()', '{0}|issn'),
                ('//oclc:datafield[@tag=\'050\']/oclc:subfield[@code=\'a\']/text()', '{0}|lcc'),
                ('//oclc:datafield[@tag=\'082\']/oclc:subfield[@code=\'a\']/text()', '{0}|ddc'),
                ('//oclc:datafield[@tag=\'010\']/oclc:subfield[@code=\'z\']/text()', '{0}|lccn'),
                ('//oclc:datafield[@tag=\'020\']/oclc:subfield[@code=\'z\']/text()', '{0}|isbn'),
                ('//oclc:datafield[@tag=\'022\']/oclc:subfield[@code=\'z\']/text()', '{0}|issn'),
                ('//oclc:datafield[@tag=\'050\']/oclc:subfield[@code=\'z\']/text()', '{0}|lcc'),
                ('//oclc:datafield[@tag=\'082\']/oclc:subfield[@code=\'z\']/text()', '{0}|dcc'),
            ],
            'contributors': [
                ('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'f\']/text()', '{0}|||manufacturer'),
                ('//oclc:datafield[@tag=\'700\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
                ('//oclc:datafield[@tag=\'710\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
                ('//oclc:datafield[@tag=\'711\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
            ],
            'languages': [('//oclc:controlfield[@tag=\'008\']/text()', '||{}')],
            'dates': [
                ('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'c\']/text()', '{0}|publication_date'),
                ('//oclc:datafield[@tag=\'264\']/oclc:subfield[@cod=\'c\']/text()', '{0}|copyright_date')
            ],
            'extent': (
                [
                    '//oclc:datafield[@tag=\'300\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'300\']/oclc:subfield[@code=\'b\']/text()',
                    '//oclc:datafield[@tag=\'300\']/oclc:subfield[@code=\'c\']/text()'
                ],
                '{0}{1}{b}'),
            'is_part_of': [
                (
                    [
                        '//oclc:datafield[@tag=\'440\']/oclc:subfield[@code=\'a\']/text()',
                        '//oclc:datafield[@tag=\'440\']/oclc:subfield[@code=\'v\']/text()'
                    ],
                    '{0}|{1}|volume'
                ),
                (
                    [
                        '//oclc:datafield[@tag=\'490\']/oclc:subfield[@code=\'a\']/text()',
                        '//oclc:datafield[@tag=\'490\']/oclc:subfield[@code=\'v\']/text()'
                    ],
                    '{0}|{1}|volume'
                )
            ],
            'abstract': ('//oclc:datafield[@tag=\'520\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            'table_of_contents': ('//oclc:datafield[@tag=\'505\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            'subjects': [(
                [
                    '//oclc:datafield[@tag=\'600\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'600\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'600\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'610\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'610\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'610\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'611\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'611\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'611\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'630\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'630\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'630\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'650\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'650\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'650\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'651\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'651\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'651\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'655\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'655\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'655\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'656\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'656\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'655\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),
                ([
                    '//oclc:datafield[@tag=\'690\']/oclc:subfield[@code=\'a\']/text()',
                    '//oclc:datafield[@tag=\'690\']/oclc:subfield[@code=\'2\']/text()',
                    '//oclc:datafield[@tag=\'690\']/oclc:subfield[@code=\'0\']/text()',
                ],
                '{0}|{1}|{2}'),

            ],
            'has_part': [(
                '//oclc:datafield[@tag=\'856\']/oclc:subfield[@code=\'z\']/text()',
                '1|{0}|oclc|text/html|{{"ebook": true, "download": false, "reader": false, "catalog": true}}'
            )]
        }

    def applyFormatting(self):
        self.record.source = 'oclcCatalog'
        self.record.source_id = self.record.identifiers[0]
        self.record.frbr_status = 'complete'

        # Parse language field
        _, _, lang_3, *_ = tuple(self.record.languages[0].split('|'))
        self.record.languages = [('||{}'.format(lang_3[35:38]))]
