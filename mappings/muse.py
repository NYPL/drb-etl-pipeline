from mappings.utils import clean_formatted_string
from .base_mapping import BaseMapping
from model import FRBRStatus, Record, Source
from uuid import uuid4
from datetime import datetime, timezone

DEFAULT_PUBLISHER = 'John Hopkins University Press||'


class MUSEMapping(BaseMapping):
    def __init__(self, muse_record):
        self.record = self.map_muse_record(muse_record)

    def map_muse_record(self, muse_record) -> Record:
        identifiers = self._get_identifiers(muse_record)
        alternative = self._get_formatted_field(muse_record, '240', ['a', 'k'], '{} {}')
        has_version = self._get_formatted_field(muse_record, '250', ['a', 'b'], '{}|')
        spatial = self._get_formatted_field(muse_record, '264', ['a'], '{}')
        extent = self._get_formatted_field(muse_record, '300', ['a', 'b', 'c'], '{}{}')
        toc = self._get_formatted_field(muse_record, '505', ['a'], '{}')

        rights = 'muse|https://creativecommons.org/licenses/by-nc/4.0/||Creative Commons Attribution-NonCommercial 4.0 International|'

        new_record = Record(
            uuid=uuid4(),
            frbr_status=FRBRStatus.TODO.value,
            cluster_status=False,
            source=Source.MUSE.value,
            source_id=list(identifiers[0].split('|'))[0],
            identifiers=identifiers,
            authors=self._get_authors(muse_record),
            title=self._get_title(muse_record),
            alternative=alternative[0] if alternative else None,
            has_version=has_version[0] if has_version else None,
            publisher=self._get_publishers(muse_record),
            spatial=spatial[0] if spatial else None,
            dates=self._get_dates(muse_record),
            languages=self._get_languages(muse_record),
            extent=extent[0] if extent else None,
            table_of_contents=toc[0] if toc else  None,
            abstract=self._get_abstracts(muse_record),
            subjects=self._get_subjects(muse_record),
            contributors=self._get_contributors(muse_record),
            is_part_of=self._get_formatted_field(muse_record, '490', ['a','v'], '{}|{}|volume'),
            has_part=self._get_formatted_field(muse_record, '856', ['u'], '1|{}|muse|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}'),
            rights=rights,
            date_created=datetime.now(timezone.utc).replace(tzinfo=None),
            date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        return new_record

    def _get_formatted_field(self, record, field, subfields, string_format):
        field_data = record.get_fields(field)
        formatted_data = []
        subfield_data = []

        for data in field_data:
            if data.is_control_field():
                subfield_data.append([getattr(data, 'data')])
            else:
                subfield_data = [data.get_subfields(subfield) if data.get_subfields(subfield) else [''] for subfield in subfields]
            
            if subfield_data == [['']]:
                continue

            for values in zip(*subfield_data):
                formatted_string = string_format.format(*values)
                formatted_data.append(clean_formatted_string(formatted_string))

        return formatted_data
    
    def _get_identifiers(self, record):
        all_identifiers = []
        
        all_identifiers.extend(self._get_formatted_field(record, '001', ['0'], '{}|muse'))
        all_identifiers.extend(self._get_formatted_field(record, '010', ['z'], '{}|lccn'))
        all_identifiers.extend(self._get_formatted_field(record, '020', ['a', 'z'], '{}{}|isbn'))
        all_identifiers.extend(self._get_formatted_field(record, '022', ['a'], '{}|issn'))
        all_identifiers.extend(self._get_formatted_field(record, '035', ['a'], '{}|oclc'))
        all_identifiers.extend(self._get_formatted_field(record, '040', ['a'], '{}|muse'))

        return [self._cleanup_identifier(id) for id in all_identifiers]
    
    def _get_authors(self, record):
        all_authors = []

        all_authors.extend(self._get_formatted_field(record, '100', ['a', 'b', 'c', 'd'], '{} {} {} {}|||true'))
        all_authors.extend(self._get_formatted_field(record, '110', ['a', 'b', 'c', 'n', 'd'], '{} {} {} {} {}|||true'))

        return all_authors
    
    def _get_title(self, record):
        title_245 = self._get_formatted_field(record, '245', ['a', 'b'], '{} {}')
        title_130 = self._get_formatted_field(record, '130', ['a'], '{}')

        all_titles = list(set(title_245 + title_130))

        return all_titles[0]
    
    def _get_publishers(self, record):
        publishers = self._get_formatted_field(record, '264', ['b'], '{}||')

        if len(publishers) < 1:
            publishers.append(DEFAULT_PUBLISHER)

        return publishers
    
    def _get_dates(self, record):
        dates = self._get_formatted_field(record, '264', ['c'], '{}|publication_date')

        if len(dates) < 1:
            publication_date = self.source['008'].data[11:15]
            dates.append('{}|publication_date'.format(publication_date))

        return dates
    
    def _get_languages(self, record):
        languages = self._get_formatted_field(record, '008', ['0'], '||{}')
        formatted_languages = [
            extracted_langauge
            for language in languages
            if (extracted_langauge := self._extract_language(language))
        ]

        return formatted_languages
    
    def _get_abstracts(self, record):
        all_abstracts = []

        all_abstracts.extend(self._get_formatted_field(record, '500', ['a'], '{}'))
        all_abstracts.extend(self._get_formatted_field(record, '504', ['a'], '{}'))
        all_abstracts.extend(self._get_formatted_field(record, '520', ['a'], '{}'))

        return all_abstracts
    
    def _get_subjects(self, record):
        all_subjects = []

        all_subjects.extend(self._get_formatted_field(record, '600', ['a', 'd', 'v', 'x', 'y', 'z', '2', '0'], '{} {} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '610', ['a', 'd', 'v', 'x', 'y', 'z', '2', '0'], '{} {} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '611', ['a', 'd', 'v', 'x', 'y', 'z', '2', '0'], '{} {} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '630', ['a', 'p', 'v', 'x', 'y', 'z', '2', '0'], '{} {} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '650', ['a', 'b', 'v', 'x', 'y', 'z', '2', '0'], '{} {} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '651', ['a', 'v', 'x', 'y', 'z', '2', '0'], '{} -- {} -- {} -- {} -- {}|{}|{}'))
        all_subjects.extend(self._get_formatted_field(record, '656', ['a', 'v', 'x', 'y', 'z', '2', '0'], '{} -- {} -- {} -- {} -- {}|{}|{}'))

        return [self._clean_up_subject_head(subject) for subject in all_subjects]
    
    def _get_contributors(self, record):
        all_contributors = []

        all_contributors.extend(self._get_formatted_field(record, '260', ['f'], '{}|||manufacturer'))
        all_contributors.extend(self._get_formatted_field(record, '700', ['a', 'b', 'c', 'd', 'e'], '{} {} {} {}|||{}'))
        all_contributors.extend(self._get_formatted_field(record, '710', ['a', 'b', 'c', 'd', 'e'], '{} {} {} {}|||{}'))
        all_contributors.extend(self._get_formatted_field(record, '711', ['a', 'e', 'j'], '{} {}|||{}'))

        return all_contributors

    def add_has_part_link(self, url, media_type, flags):
        last_item_no = int(self.record.has_part[-1][0])

        self.record.has_part.append(
            '{}|{}|muse|{}|{}'.format(last_item_no, url, media_type, flags)
        )

    def _clean_up_subject_head(self, subject):
        subject_str, *subject_metadata = subject.split('|')
        subject_parts = subject_str.split('--')

        out_parts = []

        for part in subject_parts:
            clean_parts = part.strip(' .')
            
            if clean_parts == '': continue

            out_parts.append(clean_parts)

        cleaned_subject = ' -- '.join([part for part in out_parts])

        return '|'.join([cleaned_subject] + subject_metadata)

    def _extract_language(self, language):
        _, _, marc_data, *_ = language.split('|')
        marc_data = marc_data.split(' ')

        # MARC data example: 100607s2011 mdu o 00 0 eng d
        if len(marc_data) >= 7:
            return f'||{marc_data[5]}'

        return None
    
    def _cleanup_identifier(self, identifier):
        oclc_number_prefix = '(OCoLC)'
        id, id_type = identifier.split('|')
        id = id.strip()

        if id.startswith(oclc_number_prefix):
            return f'{id[len(oclc_number_prefix):]}|{id_type}'
        
        return f'{id}|{id_type}'

    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass
