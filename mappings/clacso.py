import dataclasses
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from uuid import uuid4
import json
from typing import Optional

from model import Record, FRBRStatus, FileFlags, Part, Source
from .base_mapping import BaseMapping

HANDLE_URL = 'biblioteca-repositorio.clacso.edu.ar/handle/CLACSO'
PDF_PART_URL = "https://biblioteca-repositorio.clacso.edu.ar"

class CLACSOMapping(BaseMapping):

    def __init__(self, clacso_record, namespaces):
        self.record = self._map_to_record(clacso_record, namespaces)

    def _map_to_record(self, clacso_record, namespaces):
        medium = self.create_medium(clacso_record, namespaces)
        
        if medium is None:
            return None
        
        has_part = self.create_has_part(clacso_record, namespaces)

        if has_part is None:
            return None
        
        return Record(
            uuid=uuid4(),
            frbr_status=FRBRStatus.TODO.value,
            cluster_status=False,
            source=Source.CLACSO.value,
            source_id=self.create_source_id(clacso_record, namespaces),
            title=clacso_record.xpath('./dc:title/text()', namespaces=namespaces)[0],
            authors=self.create_authors(clacso_record, namespaces),
            medium=medium,
            identifiers=self.create_identifiers(clacso_record, namespaces),
            has_part=has_part,
            dates=self.create_dates(clacso_record, namespaces),
            date_created=datetime.now(timezone.utc).replace(tzinfo=None),
            date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
        )

    def create_authors(self, record, namespaces):
         return [f'{author}|||true' for author in record.xpath('./dc:creator/text()', namespaces=namespaces)]

    def create_source_id(self, record, namespaces):
        for identifier in record.xpath('./dc:identifier/text()', namespaces=namespaces):
            if HANDLE_URL in identifier:
                id = identifier.split('/')[-1]
                
                return f'{id}|{Source.CLACSO.value}'
    
    def create_medium(self, record, namespaces):
        for medium in record.xpath('./dc:type/text()', namespaces=namespaces):
            medium_value = medium.split('/')[-1].lower()
            
            if medium_value == 'book':
                return medium_value

    def create_identifiers(self, record, namespaces):
        return [self.format_identifier(id, 'clacso') for id in record.xpath('./dc:identifier/text()', namespaces=namespaces)]

    def create_dates(self, record, namespaces):
        years_issued = [date.split('-')[0] if '-' in date else date for date in record.xpath('./dc:date/text()', namespaces=namespaces)]
        
        return [f'{min(years_issued)}|issued']

    def create_has_part(self, record, namespaces):
        record_urls = [has_part for has_part in record.xpath('./dc:identifier/text()', namespaces=namespaces) if 'http' in has_part]
        
        for record_url in record_urls:
            if HANDLE_URL in record_url or ('view' in record_url):
                links = self.get_links(url=record_url)
                
                for link in links:
                    if '.pdf' in link.get('href', []) or 'pdf' in link.get('class', []) or 'pdf' in link.text.lower():
                        pdf_part = self.get_pdf_part(link=link)

                        if pdf_part:
                            return [pdf_part.to_string()]
    
    def get_links(self, url: str) -> list:
        try:
            response = requests.get(url, timeout=10)
        except Exception:
            return []

        clacso_page = BeautifulSoup(response.text, 'html.parser')
        
        return clacso_page.find_all('a')

    def get_pdf_part(self, link: str) -> Optional[Part]:
        pdf_link = link.get('href')
        pdf_url = f'{PDF_PART_URL}{pdf_link}' if 'bitstream/CLACSO' in pdf_link else pdf_link

        try:
            response = requests.head(pdf_url)
        except Exception:
            return None
        
        if response.status_code != 200:
            return None
        
        return Part(
            index=1, 
            url=pdf_url,
            source=Source.CLACSO.value,
            file_type='application/pdf',
            flags=json.dumps(dataclasses.asdict(FileFlags(download=True)))
        )
                            
    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass
