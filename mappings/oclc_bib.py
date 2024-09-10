from datetime import datetime, timezone
from uuid import uuid4

from model import Record

# TODO: SFR-2090: Finalize mappings


def map_oclc_brief_bib_to_record(oclc_brief_bib, related_oclc_numbers=[]) -> Record:
    return Record(
        uuid=uuid4(),
        frbr_status='complete',
        cluster_status=False,
        source='oclcClassify',
        source_id=f"{oclc_brief_bib['oclcNumber']}|oclc",
        title=oclc_brief_bib['title'],
        authors=[f"oclc_brief_bib['creator']|||true"],
        identifiers=(
            [f"{oclc_brief_bib['oclcNumber']}|oclc"] +
            [f"{oclc_number}|oclc" for oclc_number in related_oclc_numbers]
        ),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )


def map_oclc_bib_to_record(oclc_bib, related_oclc_numbers=[]) -> Record:
    identifiers = oclc_bib['identifier']
    creators = list(
        filter(
            lambda creator: creator.get('secondName') and creator.get('firstName'), 
            oclc_bib['contributor'].get('creators', [])
        )
    )
    authors = list(
        filter(
            lambda creator: 
                creator.get('isPrimary', False) or 
                {'Author', 'Writer'}.intersection(set(map(lambda relator: relator.get('term'), creator.get('relators', [])))), 
            creators
        )
    )
    contributors = list(
        filter(
            lambda creator: 
                not creator.get('isPrimary', False) or 
                (creator.get('relators') and not {'Author', 'Writer'}.intersection(set(map(lambda relator: relator.get('term'), creator['relators'])))), 
            creators
        )
    )

    return Record(
        uuid=uuid4(),
        frbr_status='complete',
        cluster_status=False,
        source='oclcClassify',
        source_id=f"{identifiers['oclcNumber']}|oclc",
        title=oclc_bib['title']['mainTitles'][0]['text'],
        subjects=[f"{subject['subjectName']['text']}||{subject.get('vocabulary', '')}" for subject in oclc_bib.get('subjects', [])],
        authors=[f"{author['secondName']['text']}, {author['firstName']['text']}|||true" for author in authors],
        contributors=[
            f"{contributor['secondName']['text']}, {contributor['firstName']['text']}|||{', '.join(list(map(lambda relator: relator.get('term', ''), contributor.get('relators', []))))}" for contributor in contributors
        ],
        identifiers=(
            [f"{identifiers['oclcNumber']}|oclc"] +
            [f"{oclc_number}|oclc" for oclc_number in related_oclc_numbers]
        ),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )
