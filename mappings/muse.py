from mappings.marc import MARCMapping

class MUSEMapping(MARCMapping):
    def __init__(self, source):
        super(MUSEMapping, self).__init__(source, {})
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('001', '{0}|muse'),
                ('010', '{z}|lccn'),
                ('020', '{a}{z}|isbn'),
                ('022', '{a}|issn'),
                ('035', '{a}|oclc'),
                ('040', '{a}|muse')
            ],
            'authors': [
                ('100', '{a} {b} {c} {d}|||true'),
                ('110', '{a} {b} {c} {n} {d}|||true'),
            ],
            'title': [
                ('245', '{a} {b}'),
                ('130', '{a}')
            ],
            'alternative': [
                ('240', '{a} {k}') # Uniform Title
            ],
            'has_version': ('250', '{a} {b}|'),
            'publisher': [('264', '{b}||')],
            'spatial': ('264', '{a}'),
            'dates': [
                ('264', '{c}|publication_date')
            ],
            'languages': [('008', '||{0}')],
            'extent': ('300', '{a}{b}{c}'),
            'table_of_contents': ('505', '{a}'),
            'abstract': [
                ('500', '{a}'),
                ('504', '{a}'),
                ('520', '{a}'),
            ],
            'subjects': [
                ('600', '{a} {d} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('610', '{a} {d} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('611', '{a} {d} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('630', '{a} {p} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('650', '{a} {b} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('651', '{a} -- {v} -- {x} -- {y} -- {z}|{2}|{0}'),
                ('656', '{a} -- {v} -- {x} -- {y} -- {z}|{2}|{0}')
            ],
            'contributors': [
                ('260', '{f}|||manufacturer'),
                ('700', '{a} {b} {c} {d}|||{e}'),
                ('710', '{a} {b} {c} {d}|||{e}'),
                ('711', '{a} {e}|||{j}'),
            ],
            'is_part_of': ('490', '{a}|{v}|volume'),
            'has_part': [
                ('856', '1|{u}|muse|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}')
            ]
        }

    def applyFormatting(self):
        self.record.source = 'muse'
        self.record.source_id = list(self.record.identifiers[0].split('|'))[0]

        # Take first title as they are in order of preference
        self.record.title = self.record.title[0]

        self.record.id = [self.clean_identifier(id) for id in self.record.identifiers]

        # Extract language code from 008 fixed data field
        self.record.languages = [self.extractLanguage(l) for l in self.record.languages]

        # Extract publication date from 008 fixed field if 264 field is missing
        if len(self.record.dates) < 1:
            pubDate = self.source['008'].data[11:15]
            self.record.dates.append('{}|publication_date'.format(pubDate))

        # If publisher missing, assume JHU
        if len(self.record.publisher) < 1:
            self.record.publisher.append('John Hopkins University Press||')

        # Clean up subjects to remove spots for missing subheadings
        self.record.subjects = [
            self.cleanUpSubjectHead(s)
            for s in self.record.subjects
        ]

        # Add Rights statement
        self.record.rights = '{}|{}||{}|'.format(
            'muse', 'https://creativecommons.org/licenses/by-nc/4.0/',
            'Creative Commons Attribution-NonCommercial 4.0 International'
        )

    def cleanUpSubjectHead(self, subject):
        subjectStr, *subjectMeta = subject.split('|')
        subjectParts = subjectStr.split('--')

        outParts = []

        for part in subjectParts:
            cleanPart = part.strip(' .')
            
            if cleanPart == '': continue

            outParts.append(cleanPart)

        cleanSubject = ' -- '.join([p for p in outParts])

        return '|'.join([cleanSubject] + subjectMeta)

    def extractLanguage(self, language):
        _, _, marcData, *_ = language.split('|')
        return '||{}'.format(marcData[35:38])

    def addHasPartLink(self, url, mediaType, flags):
        lastItemNo = int(self.record.has_part[-1][0])

        self.record.has_part.append(
            '{}|{}|muse|{}|{}'.format(lastItemNo, url, mediaType, flags)
        )

    def clean_identifier(self, identifier):
        oclc_number_prefix = '(OCoLC)'

        if identifier.startswith(oclc_number_prefix):
            return identifier[len(oclc_number_prefix):]
        
        return identifier 
