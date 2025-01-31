from typing import Optional

from model import Record


def map_nypl_bib_to_record(bib: dict) -> Record:
    language: dict = bib.get('lang', {})

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
                get_identifier(bib, 'id', 'nypl'),
                get_identifier(bib, 'issn', 'issn'),
                get_identifier(bib, 'lccn', 'lccn'),
                get_identifier(bib, 'oclc', 'oclc')
            ] if identifier
        ]
    )

    return record

def get_identifier(bib: dict, id_name: str, id_type: str) -> Optional[None]:
    id = bib.get(id_name)

    return (id and f'{id}|{id_type}') or None
