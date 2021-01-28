import re

from mappings.marc import MARCMapping

class DOABMapping(MARCMapping):
    SUBJ_IND_2 = {
        0: 'lcsh', 1: 'lcch', 2: 'msh', 3: 'nalsaf', 4: '', 5: 'csh', 6: 'rvm'
    }

    def __init__(self, source, statics):
        super(DOABMapping, self).__init__(source, statics)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('001', '{0}|doab'),
                ('010', '{a}{z}|lccn'),
                ('020', '{a}{z}|isbn'),
                ('022', '{a}{z}|issn'),
                ('024', '{a}|{s2}'),
                ('035', '{a}{z}|oclc'),
                ('040', '{a}{z}|doab')
            ],
            'authors': [
                ('100', '{a} {b} {c} {d}|||true'),
                ('110', '{a} {b} {c} {n} {d}|||true'),
                ('111', '{a} {e}|||true')
            ],
            'title': ('245', '{a} {b}'),
            'alternative': [
                ('210', '{a}'),
                ('222', '{a}'),
                ('240', '{a} {k}'), # Uniform Title
                ('242', '{a}'),
                ('246', '{a}'),
                ('247', '{a}')
            ],
            'has_version': ('250', '{a} {b}|'),
            'publisher': ('260', '{b}||'),
            'spatial': ('264', '{a}'),
            'dates': [
                ('260', '{c}|publication_date'),
                ('264', '{c}|copyright_date')
            ],
            'languages': [('546', '{a}||')],
            'extent': ('300', '{a}{b}{c}{e}{f}'),
            'table_of_contents': ('505', '{a}'),
            'abstract': [
                ('500', '{a}'),
                ('504', '{a}'),
                ('520', '{a}'),
            ],
            'subjects': [
                ('600', '{a} {b} {c} {d} {q} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('610', '{a} {b} {c} {d} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('611', '{a} {d} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('630', '{a} {p} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('648', '{a} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('650', '{a} {b} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('651', '{a} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('655', '{a} {b} {c} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('656', '{a} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}'),
                ('657', '{a} -- {v} -- {x} -- {y} -- {z}|{ind2}|{0}')
            ],
            'contributors': [
                ('260', '{f}|||manufacturer'),
                ('700', '{a} {b} {c} {d}|||{s4}'),
                ('710', '{a} {b} {c} {d}|||{s4}'),
                ('711', '{a} {e}|||{s4}'),
            ],
            'is_part_of': ('490', '{a}|{v}|volume'),
            'has_part': [
                ('856', '1|{u}|doab|text/html|{{"reader": false, "download": false, "catalog": false}}')
            ]
        }

    def applyFormatting(self):
        if len(self.record.identifiers) == 0: self.raiseMappingError('Malformed DOAB record')

        self.record.source = 'doab'
        self.record.source_id = list(self.record.identifiers[0].split('|'))[0]

        # Clean up languages (splitting if necessary)
        cleanLanguages = []
        for language in self.record.languages:
            cleanLanguages.extend(self.cleanAndSplitLanguage(language))
        self.record.languages = cleanLanguages

        # Clean up subjects to remove spots for missing subheadings
        self.record.subjects = [
            self.cleanUpSubjectHead(s)
            for s in self.record.subjects
        ]

        # Lookup MARC contributor codes and transform to full strings
        self.record.contributors = [
            self.parseContributorCode(c) for c in self.record.contributors
        ]

        # Add Rights statement
        self.record.rights = '{}|{}||{}|'.format(
            'doab', 'https://creativecommons.org/licenses/by-nc-nd/4.0/',
            'Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International'
        )

    def parseContributorCode(self, contributor):
        *contribComponents, role = contributor.split('|')
        lcRelation = self.staticValues['marc']['contributorCodes'].get(role, 'contributor')
        return '{}|{}|{}|{}'.format(*contribComponents, lcRelation)

    def cleanUpSubjectHead(self, subject):
        subjectStr, authority, authNo = subject.split('|')
        subjectParts = subjectStr.split('--')

        outParts = []

        for part in subjectParts:
            cleanPart = part.strip(' .')
            
            if cleanPart == '': continue

            outParts.append(cleanPart)

        cleanSubject = ' -- '.join([p for p in outParts])

        try:
            authority = self.SUBJ_IND_2.get(int(authority), '')
        except ValueError:
            authority = ''

        return '{}|{}|{}'.format(cleanSubject, authority, authNo)

    def cleanAndSplitLanguage(self, language):
        lang, *_ = language.split('|')
        langs = re.split(r'/|\|', lang)

        return [
            '||{}'.format(l) if len(l) == 3 else '{}||'.format(l)
            for l in langs
        ]
