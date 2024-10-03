from mappings.marc import MARCMapping

DEFAULT_PUBLISHER = 'John Hopkins University Press||'


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

        self.record.identifiers = [self.cleanup_identifier(id) for id in self.record.identifiers]
        
        self.record.languages = [
            extracted_langauge
            for language in self.record.languages
            if (extracted_langauge := self.extract_language(language))
        ]

        if len(self.record.dates) < 1:
            publication_date = self.source['008'].data[11:15]
            self.record.dates.append('{}|publication_date'.format(publication_date))
        
        if len(self.record.publisher) < 1:
            self.record.publisher.append(DEFAULT_PUBLISHER)

        self.record.subjects = [self.clean_up_subject_head(subject) for subject in self.record.subjects]

        self.record.rights = '{}|{}||{}|'.format(
            'muse', 
            'https://creativecommons.org/licenses/by-nc/4.0/',
            'Creative Commons Attribution-NonCommercial 4.0 International'
        )

    def clean_up_subject_head(self, subject):
        subject_str, *subject_metadata = subject.split('|')
        subject_parts = subject_str.split('--')

        out_parts = []

        for part in subject_parts:
            clean_parts = part.strip(' .')
            
            if clean_parts == '': continue

            out_parts.append(clean_parts)

        cleaned_subject = ' -- '.join([part for part in out_parts])

        return '|'.join([cleaned_subject] + subject_metadata)

    def extract_language(self, language):
        _, _, marc_data, *_ = language.split('|')
        marc_data = marc_data.split(' ')

        # MARC data example: 100607s2011 mdu o 00 0 eng d
        if len(marc_data) >= 7:
            return f'||{marc_data[5]}'

        return None

    def add_has_part_link(self, url, media_type, flags):
        last_item_no = int(self.record.has_part[-1][0])

        self.record.has_part.append(
            '{}|{}|muse|{}|{}'.format(last_item_no, url, media_type, flags)
        )

    def cleanup_identifier(self, identifier):
        oclc_number_prefix = '(OCoLC)'
        id, id_type = identifier.split('|')
        id = id.strip()

        if id.startswith(oclc_number_prefix):
            return f'{id[len(oclc_number_prefix):]}|{id_type}'
        
        return f'{id}|{id_type}'
