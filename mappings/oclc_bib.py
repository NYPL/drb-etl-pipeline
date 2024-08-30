from datetime import datetime, timezone
from uuid import uuid4

from model import Record
from .core import Core

class oclc_mapping_v2(Core):
    def __init__(self, oclc_bib, related_oclc_numbers=[]):
        self.record = Record(uuid=uuid4(),
        frbr_status='complete',
        cluster_status=False,
        source='oclcClassify',
        # TODO: SFR-2090: Determine if this should the oclc number of owi
        source_id=f"{oclc_bib['oclcNumber']}|oclc",
        title=oclc_bib['title'],
        # TODO: SFR-2090: Should we get the subjects facet?
        subjects=[],
        authors=[oclc_bib['creator']],
        # TODO: SFR-2090: Split creators into authors and contributors
        contributors=[],
        languages=[oclc_bib['language']],
        # TODO: SFR-2090: Determine which dates to pull if any
        dates=[],
        # TODO: SFR-2090: Determine which identifiers to add
        identifiers=(
            [f"{oclc_bib['oclcNumber']}|oclc"] +
            [f"{issn}|issn" for issn in oclc_bib.get('issns', [])] +
            [f"{isbn}|isbn" for isbn in oclc_bib.get('isbns', [])] +
            [f"{oclc_number}|oclc" for oclc_number in related_oclc_numbers]
        ),
        publisher=oclc_bib.get('publisher', None),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass