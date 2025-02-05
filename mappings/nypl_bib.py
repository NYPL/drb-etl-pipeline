from collections import defaultdict
from typing import Optional

from model import Record


def map_nypl_bib_to_record(bib: dict) -> Record:
    language: dict = bib.get('lang', {})
    marc_fields: dict = get_marc_fields(bib)
    publication_details = marc_fields.get('260', [])

    record = Record(
        title=bib.get('title'),
        authors=[f"{bib.get('author')}|||true"],
        languages=[f"{language.get('name')}||{language.get('code')}"],
        dates=[
            f"{bib.get('publish_year')}|publication_date",
            f"{bib.get('catalog_date')}|catalog_date"
        ],
        spatial=bib.get('country', {}).get('name'),
        identifiers=get_identifiers(bib, marc_fields),
        publisher=[f"{publication_detail.get('b')}||" for publication_detail in publication_details if publication_detail.get('b')],
        contributors=get_contributers(marc_fields)
    )

    print(record.identifiers)

    return record


def get_marc_fields(bib: dict) -> dict:
    marc_fields = {}

    for var_field in bib.get('var_fields', []):
        sub_fields = {sub_field.get('tag'): sub_field.get('content') for sub_field in (var_field.get('subfields', []) or [])}

        if var_field.get('marcTag') is not None:
            marc_fields[var_field.get('marcTag')] = marc_fields.get(var_field.get('marcTag'), []) + [sub_fields]
    
    return marc_fields


def get_identifiers(bib: dict, marc_fields: dict) -> list[str]:
    identifiers_mapping = {
        '010': ('{a}|lccn'),
        '020': ('{a}|isbn'),
        '022': ('{a}|issn'),
        '028': ('{a}|{b}'),
        '035': ('{a}|scn'),
        '050': ('{a} {b}|lcc'),
        '060': ('{a}|nlcmn'),
        '074': ('{a}|gpoin'),
        '086': ('{a}|gdcn')
    }

    identifiers = set(
        [
            f"{bib.get('id', '')}|nypl",
            f"{bib.get('issn', '')}|issn",
            f"{bib.get('lccn', '')}|lccn",
            f"{bib.get('oclc', '')}|oclc",
            f"{bib.get('isbn', '')}|isbn"
        ] +
        [
            f"{mapping.format_map(defaultdict(str, marc_field_entry))}"
            for tag, mapping in identifiers_mapping.items()
            for marc_field_entry in marc_fields.get(tag, [])
            if mapping
        ]
    )

    return [id for id in identifiers if id.split('|')[0]]


def get_contributers(marc_fields: dict) -> list[str]:
    contributor_mapping = {
        '260': ('{f}|||manufacterer'),
        '700': ('{a}|||{e}'),
        '710': ('{a} {b}|||{e}'),
        '711': ('{a}|||{e}')
    }

    contributors = [
        f"{mapping.format_map(defaultdict(str, marc_field_entry))}"
        for tag, mapping in contributor_mapping.items()
        for marc_field_entry in marc_fields.get(tag, [])
        if mapping
    ]

    return [contributor for contributor in contributors if contributor.split('|')[0]]

