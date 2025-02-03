from typing import Optional

from model import Record


def map_nypl_bib_to_record(bib: dict) -> Record:
    language: dict = bib.get('lang', {})
    marc_fields: dict = get_marc_fields(bib)

    record = Record(
        title=bib.get('title'),
        authors=[f"{bib.get('author')}|||true"],
        languages=[f"{language.get('name')}||{language.get('code')}"],
        dates=[
            f"{bib.get('publish_year')}|publication_date",
            f"{bib.get('catalog_date')}|catalog_date"
        ],
        spatial=bib.get('country', {}).get('name'),
        identifiers=[
            identifier for identifier in [
                get_identifier(bib.get('id'), 'nypl'),
                get_identifier(bib.get('issn'), 'issn'),
                get_identifier(bib.get('lccn'), 'lccn'),
                get_identifier(bib.get('oclc'), 'oclc'),
                get_identifier(marc_fields.get('010', {}).get('a'), 'lccn'),
                get_identifier(marc_fields.get('020', {}).get('a'), 'isbn'),
                get_identifier(marc_fields.get('022', {}).get('a'), 'issn'),
                get_identifier(
                    marc_fields.get('028', {}).get('a'), 
                    marc_fields.get('028', {}).get('b')
                ),
                get_identifier(marc_fields.get('035', {}).get('a'), 'scn'),
                get_identifier(
                    f"{marc_fields.get('050', {}).get('a')} {marc_fields.get('050', {}).get('b')}",
                    'lcc'
                ),
                get_identifier(marc_fields.get('060', {}).get('a'), 'nlmcn'),
                get_identifier(marc_fields.get('074', {}).get('a'), 'gpoin'),
                get_identifier(marc_fields.get('086', {}).get('a'), 'gdcn')
            ] if identifier
        ],
        publisher=[f"{marc_fields.get('260', {}).get('b')}||"],
        contributors=[
            f"{marc_fields.get('260', {}).get('f')}|||manufacturer",
            f"{marc_fields.get('700', {}).get('a')}|||{marc_fields.get('700', {}).get('e')}",
            f"{marc_fields.get('710', {}).get('a')} {marc_fields.get('710', {}).get('b')}|||{marc_fields.get('710', {}).get('e')}",
            f"{marc_fields.get('711', {}).get('a')} {marc_fields.get('711', {}).get('b')}|||{marc_fields.get('711', {}).get('e')}"
        ]
    )

    print(record.contributors)

    return record


def get_identifier(id: str, id_type: str) -> Optional[str]:
    return (id and f'{id}|{id_type}') or None


def get_marc_fields(bib: dict) -> dict:
    marc_fields = {}

    for var_field in bib.get('var_fields', []):
        for sub_field in (var_field.get('subfields', []) or []):
            var_field[sub_field.get('tag')] = sub_field.get('content')
        
        marc_fields[var_field.get('marcTag', 'XXX')] = var_field
    
    return marc_fields
