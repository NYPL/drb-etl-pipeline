import json

from constants.get_constants import get_constants
from model import FileFlags, Record, Source, Part
from mappings.formatter import map_source_record
from mappings.record import map_to_record


constants = get_constants()
NYPL_BIB_MAPPING = {
    'title': ('title', '{0}'),
    'alternative': [
        ('246', '{a} {b} {p}'),
        ('247', '{a} {f}')
    ],
    'authors': [('author', '{0}|||true')],
    'languages': [('lang', '{name}||{code}')],
    'dates': [
        ('publish_year', '{0}|publication_date'),
        ('catalog_date', '{0}|catalog_date')
    ],
    'spatial': ('country', '{name}'),
    'source_id': ('id', '{0}|nypl'),
    'identifiers': [
        ('id', '{0}|nypl'),
        ('issn', '{0}|issn'),
        ('lccn', '{0}|lccn'),
        ('oclc', '{0}|oclc'),
        ('isbn', '{0}|isbn'),
        ('010', '{a}|lccn'),
        ('020', '{a}|isbn'),
        ('022', '{a}|issn'),
        ('028', '{a}|{b}'),
        ('035', '{a}|scn'),
        ('050', '{a} {b}|lcc'),
        ('060', '{a}|nlmcn'),
        ('074', '{a}|gpoin'),
        ('086', '{a}|gdcn')
    ],
    'publisher': [('260', '{b}||')],
    'contributors': [
        ('260', '{f}|||manufacturer'),
        ('700', '{a}|||{e}'),
        ('710', '{a} {b}|||{e}'),
        ('711', '{a} {b}|||{e}')
    ],
    'has_version': ('250', '{a}|'),
    'extent': ('300', '{a}{b}{c}'),
    'is_part_of': [
        ('440', '{a}|{v}|volume'),
        ('490', '{a}|{v}|volume')
    ],
    'abstract': [
        ('500', '{a}'),
        ('520', '{a} {b}')
    ],
    'table_of_contents': ('505', '{a}'),
    'subjects': [
        ('600', '{a} {d} -- {t} -- {v}|lcsh|'),
        ('610', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|'),
        ('611', '{a} -- {v}|lcsh|'),
        ('630', '{a} -- {p} -- {v}|lcsh|'),
        ('650', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|'),
        ('651', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|'),
        ('655', '{a}||'),
        ('656', '{a}||'),
        ('690', '{a} -- {b} -- {v} -- {x} -- {z}|lcsh|'),
    ],
    'has_part': [('856', '1|{u}|nypl|text/html|{{"catalog": false, "download": false, "reader": false, "embed": true}}')],
}


def map_nypl_bib_to_record(nypl_bib: dict, nypl_bib_items: list[dict], location_codes: dict) -> Record:
    marc_fields = get_marc_fields(nypl_bib)
    nypl_bib.update(marc_fields)

    mapped_source_record = map_source_record(nypl_bib, mapping=NYPL_BIB_MAPPING)
    
    has_part = clean_has_part(mapped_source_record.get('has_part', []), mapped_source_record.get('source_id'))
    coverage, has_part = add_requestable_parts(nypl_bib_items, has_part, mapped_source_record.get('source_id'))

    return map_to_record(
        {
            **mapped_source_record,
            'identifiers': clean_identifiers(mapped_source_record.get('identifiers', [])),
            'subjects': clean_subjects(mapped_source_record.get('subjects', [])),
            'contributors': clean_contributors(mapped_source_record.get('contributors', [])),
            'coverage': coverage,
            'has_part': has_part
        }, 
        Source.NYPL
    )


def get_marc_fields(bib: dict) -> dict:
    marc_fields = {}

    for var_field in bib.get('var_fields', []):
        sub_fields = {sub_field.get('tag'): sub_field.get('content') for sub_field in (var_field.get('subfields', []) or [])}

        if var_field.get('marcTag') is not None:
            marc_fields[var_field.get('marcTag')] = marc_fields.get(var_field.get('marcTag'), []) + [sub_fields]
    
    return marc_fields


def clean_identifiers(identifiers: list[str]) -> list[str]:
    return list({
        id.replace('(OCoLC)', '').replace('scn', 'oclc') if isinstance(id, str) and '(OCoLC)' in id else id 
        for id in identifiers
        if id.split('|')[0]
    })


def clean_subjects(subjects: list[str]) -> list[str]:
    return [
        '{}|{}'.format('--'.join([part.strip() for part in subject.split('|')[0].split('--') if part.strip()]), *subject.split('|')[1:])
        for subject in subjects
        if subject.split('|')[0]
    ]

def clean_contributors(contributors: list[str]) -> list[str]:
    return [
        '{}|{}|{}|{}'.format(*contributor_data[:-1], constants['lc']['relators'].get(contributor_data[-1], 'Contributor'))
        for contributor in contributors
        for contributor_data in [contributor.split('|')]
        if contributor_data[0]
    ]

def clean_has_part(has_part: list[str], source_id: str) -> list[str]:
    if len(has_part) == 0:
        catalog_part = Part(
            index=1, 
            url=f'https://www.nypl.org/research/collections/shared-collection-catalog/bib/b{source_id}',
            source=Source.NYPL.value,
            file_type='application/html+catalog',
            flags=json.dumps(FileFlags(catalog=True))
        )
        has_part.append(catalog_part.to_string())

    return has_part


def add_requestable_parts(bib_items: list[dict], has_part: list[str], location_codes: dict, source_id: str) -> tuple:
    coverage = []
    requestable_items = [
        item 
        for item in bib_items 
        if location_codes.get(item.get('location', {}).get('code', {}), {}).get('requestable')
    ]

    for item in requestable_items:
        location_metadata = item.get('location')
        index = len(has_part) + 1
        requestable_item_part = Part(
            index=index,
            url=f"http://www.nypl.org/research/collections/shared-collection-catalog/hold/request/b{source_id}-i{item.get('id')}",
            source=Source.NYPL.name,
            file_type='applicaton/x.html+edd',
            flags=FileFlags(edd=True, nypl_login=True)
        )

        coverage.append(f"{location_metadata.get('code')}|{location_metadata.get('name')}|{index}")
        has_part.append(requestable_item_part.to_string())

    return (coverage, has_part)
