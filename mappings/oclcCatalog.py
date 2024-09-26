import json
import re
import requests
from requests.exceptions import ReadTimeout, HTTPError

from mappings.xml import XMLMapping
from logger import createLog

logger = createLog(__name__)


class CatalogMapping(XMLMapping):
    EBOOK_REGEX = {
        'gutenberg': r'gutenberg.org\/ebooks\/([0-9]+)',
        'internetarchive': r'archive.org\/details\/([a-z0-9]+)$',
        'hathitrust': r'catalog.hathitrust.org\/api\/volumes\/([a-z]{3,6}\/[a-zA-Z0-9]+)\.html'
    }

    def __init__(self, source, namespace, statics):
        super(CatalogMapping, self).__init__(source, namespace, statics)
        self.mapping = self.createMapping()

    def createMapping(self):
        return {
            # Maps to title -> mainTitles Main Titles [v245sa,b,c,f,g,k,n,p,s]
            'title': ('//oclc:datafield[@tag=\'245\']/oclc:subfield[@code=\'a\' or @code=\'b\']/text()', '{0} {1}'),
            # No mapping
            'alternative': [
                ('//oclc:datafield[@tag=\'210\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'222\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'242\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'246\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
                ('//oclc:datafield[@tag=\'247\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            ],
            # Maps to contributor
            # [v100sa,q,b,c,d,e,4,k v110sa,q,b,c,d,e,4,k,n v111sa,q,c,d,e,j,k,n v700sa,q,b,c,d,e,4,k v710sa,q,b,c,d,e,4,k,n v720sa v711 sa,q,c,d,e,j,k,n v790sa,q,c,d,e,j,k,n v791sa,q,b,c,d,e,4,k v792sa,b,q,c, d,e,j,k,n v796 sa,q,b,c,d,e,4,k v797sa,q,b,c,d,e,4,k,n v798sa,b,q,c, d,e,j,k,n]
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
            # Maps to publisher [v260sa,b v264sa,b v880sa,b]
            'publisher': [('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'b\']/text()', '{0}||')],
            # Maps to identifer 
            'identifiers': [
                ('//oclc:controlfield[@tag=\'001\']/text()', '{0}|oclc'),
                # Library of Congress Control Number [v010sa]
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
            # Maps to contributor
            'contributors': [
                # Maps to publisher [v260sa,b v264sa,b v880sa,b]
                ('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'f\']/text()', '{0}|||manufacturer'),
                ('//oclc:datafield[@tag=\'700\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
                ('//oclc:datafield[@tag=\'710\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
                ('//oclc:datafield[@tag=\'711\']/oclc:subfield[@code=\'f\']/text()', '{0}|||contributor'),
            ],
            # Maps to language Language of the item [v041sa,j] - different MARC field
            'languages': [('//oclc:controlfield[@tag=\'008\']/text()', '||{}')],
            # Maps to date
            'dates': [
                # Date of Publication [v260sc || c008(bytes 07-14) || v264sc || v362sa]
                ('//oclc:datafield[@tag=\'260\']/oclc:subfield[@code=\'c\']/text()', '{0}|publication_date'),
                ('//oclc:datafield[@tag=\'264\']/oclc:subfield[@cod=\'c\']/text()', '{0}|copyright_date')
            ],
            # https://www.loc.gov/marc/bibliographic/bd300.html
            # Maps to description -> physical description, e.g. [v300sa,b,c,d,e,f,g,3]
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
                # Title - seriesTitles [(v490,v810,v830 - sa)]
                (
                    [
                        '//oclc:datafield[@tag=\'490\']/oclc:subfield[@code=\'a\']/text()',
                        '//oclc:datafield[@tag=\'490\']/oclc:subfield[@code=\'v\']/text()'
                    ],
                    '{0}|{1}|volume'
                )
            ],
            # Maps to description -> Abstract [v520sa,b,c] 
            'abstract': ('//oclc:datafield[@tag=\'520\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            # Maps to description -> content Formatted Contents Note [v505sa,t,r,g,u]
            'table_of_contents': ('//oclc:datafield[@tag=\'505\']/oclc:subfield[@code=\'a\']/text()', '{0}'),
            # Maps to subjects Subjects [v600sa,b,c,d,n,v,x,y,z,e,j,4 v610sa,b,n,v,x,y,z,e,j,4 v611sa,c,d,n,v,x,y,z,e,j,4 v630sa,d,e,f,k,l,m,n,o,d,p,r,s,v,x,y,z,e,j,4 v650sa,b,x,y,z,v,e,j,4 v651sa,x,y,z,v,e,j,4 v655sa,b,c,v,x,y,z,e,j,4 v648sa,v,w,x,y,z,e,j,4 v653sa,e,j,4 v656sa,k,v,x,y,z,3,e,j,4 v657sa,v,x,y,z,3,e,j,4 (v690,v691,v695,v696,v697,v698,v699 sa,b,c,d,e,f,k,l,m,n,o,p,r,s,v,x,y,z,e,j,4)]
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
            # https://www.loc.gov/marc/bibliographic/bd856.html
            # Electronic location and access
            # Maps to digitalAccessAndLocations -> URI of resource [v856su]
            'has_part': [(
                [
                    '//oclc:datafield[@tag=\'856\']/oclc:subfield[@code=\'u\']/text()',
                    '//oclc:datafield[@tag=\'856\']/@ind1'
                ],
                '1|{0}|oclc|text/html|{{"download": false, "reader": false, "catalog": false, "embed": true, "marcInd1": "{1}"}}'
            )]
        }

    def applyFormatting(self):
        self.record.source = 'oclcCatalog'
        self.record.source_id = self.record.identifiers[0]
        self.record.frbr_status = 'complete'
        
        _, _, lang_3, *_ = tuple(self.record.languages[0].split('|'))
        self.record.languages = [('||{}'.format(lang_3[35:38]))]
        
        self.record.has_part = self.record.has_part[:10]

        self.record.has_part = list(filter(None, [
            self.parseLink(p) for p in self.record.has_part
        ]))

    def parseLink(self, part):
        partNo, partLink, partSource, partFormat, partFlags = part.split('|')

        partDict = json.loads(partFlags)

        if partDict['marcInd1'] != '4' or partLink == '':
            return None

        for source, sourceRegex in self.EBOOK_REGEX.items():
            sourceMatch = re.search(sourceRegex, partLink)

            if sourceMatch:
                sourceID = sourceMatch.group(1)

                if source == 'internetarchive':
                    if self.checkIAReadability(partLink) is False:
                        return None

                    # TODO
                    # 1) Parse HathiTrust Links
                    # 2) Parse Project Gutenberg Links
                    logger.debug('Adding IA Link {}'.format(partLink))

                self.record.identifiers.append('{}|{}'.format(
                    sourceID, source
                ))

                del partDict['marcInd1']
                return '|'.join([
                    partNo,
                    partLink,
                    partSource,
                    partFormat,
                    json.dumps(partDict)
                ])

    def checkIAReadability(self, iaURL):
        metadataURL = iaURL.replace('details', 'metadata')

        try:
            metadataResp = requests.get(metadataURL, timeout=5)
            metadataResp.raise_for_status()
        except (ReadTimeout, HTTPError) as e:
            logger.debug('Unable to read InternetArchive link')
            logger.error(e)
            return False

        iaData = metadataResp.json()
        iaAccessStatus = iaData['metadata']\
            .get('access-restricted-item', 'false')

        return iaAccessStatus == 'false'
