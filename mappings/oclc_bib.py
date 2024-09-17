from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from model import Record
from .core import Core


class OCLCBibMapping(Core):
    def __init__(self, oclc_bib, related_oclc_numbers=[]):
        identifiers = oclc_bib['identifier']
        creators = self._get_creators(oclc_bib)
        authors = self._get_authors(creators)
        contributors = self._get_contributors(creators)

        self.record = Record(
            uuid=uuid4(),
            frbr_status='complete',
            cluster_status=False,
            source='oclcClassify',
            source_id=f"{oclc_bib['work']['id']}|owi",
            title=oclc_bib['title']['mainTitles'][0]['text'],
            subjects=self._map_subjects(oclc_bib),
            authors=self._map_authors(authors),
            contributors=self._map_contributors(contributors),
            identifiers=(
                [f"{oclc_bib['work']['id']}|owi"] +
                [f"{identifiers['oclcNumber']}|oclc"] +
                [f"{oclc_number}|oclc" for oclc_number in related_oclc_numbers]
            ),
            date_created=datetime.now(timezone.utc).replace(tzinfo=None),
            date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
        )

    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass

    def _get_creators(self, oclc_bib):
        if not oclc_bib.get('contributor'): 
            return None

        return list(
            filter(
                lambda creator: creator.get('secondName') or creator.get('firstName'), 
                oclc_bib['contributor'].get('creators', [])
            )
        )
    
    def _get_authors(self, creators):
        if not creators:
            return None

        return list(
            filter(
                lambda creator: 
                    creator.get('isPrimary', False) or 
                    self._is_author(creator), 
                creators
            )
        )
    
    def _get_contributors(self, creators):
        if not creators:
            return None

        return list(
            filter(
                lambda creator: 
                    not creator.get('isPrimary', False) and 
                    not self._is_author(creator), 
                creators
            )
        )
    
    def _is_author(self, creator):
        for role in set(map(lambda relator: relator.get('term').lower(), creator.get('relators', []))):
            if 'author' in role.lower() or 'writer' in role.lower():
                return True
        
        return False
    
    def _map_subjects(self, oclc_bib) -> list[str]:
        return [f"{subject['subjectName']['text']}||{subject.get('vocabulary', '')}" for subject in oclc_bib.get('subjects', [])]
    
    def _map_authors(self, authors) -> Optional[list[str]]:
        if not authors:
            return None
        
        return [f'{author_name}|||true' for author in authors if (author_name := self._get_author_name(author))]
    
    def _get_author_name(self, author) -> str:
        first_name = self._get_name(author.get('firstName'))
        second_name = self._get_name(author.get('secondName'))

        if not first_name and not second_name:
            return None

        if first_name and second_name:
            return f'{second_name}, {first_name}'
        
        return f'{first_name or second_name}'
        
    def _get_name(self, name_data) -> str:
        if not name_data:
            return None

        return name_data.get('text') or name_data.get('romanizedText') or None
    
    def _map_contributors(self, contributors) -> Optional[list[str]]:
        if not contributors:
            return None

        return [
            f"{contributor['secondName']['text']}, {contributor['firstName']['text']}|||{', '.join(list(map(lambda relator: relator.get('term', ''), contributor.get('relators', []))))}"
            for contributor in contributors
        ]
