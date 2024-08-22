from datetime import datetime, timezone
from uuid import uuid4

from model import Record


def map_oclc_bib_to_record(oclc_bib, related_oclc_numbers=[]) -> Record:
    return Record(
        uuid=uuid4(),
        frbr_status='complete',
        cluster_status=False,
        source='oclcClassify',
        # TODO: should this be an owi number? 
        source_id=f"{oclc_bib['oclcNumber']}|oclc",
        title=oclc_bib['title'],
        # TODO: explicitly request subject search facet
        subjects=[],
        authors=[oclc_bib['creator']],
        # TODO: split contributors from creator field
        contributors=[],
        languages=[oclc_bib['language']],
        # TODO: previously we weren't pulling in dates but we could here
        dates=[],
        # TODO: should we include merged OCLC numbers? 
        identifiers=[f"{oclc_bib['oclcNumber']}|oclc"] + \
            map(lambda issn: f"{issn}|issn", oclc_bib['issns']) if oclc_bib['issns'] else [] + \
            map(lambda isbn: f"{isbn}|isbn", oclc_bib['isbns']) if oclc_bib['isbns'] else [] + \
            map(lambda oclc_number: f"{oclc_number}|oclc", related_oclc_numbers),
        publisher=[oclc_bib['publisher']],
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )
