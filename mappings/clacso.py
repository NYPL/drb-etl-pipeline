import re
import dataclasses
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from uuid import uuid4
import json

from model import Record, FRBRStatus, FileFlags, Part, Source
from .base_mapping import BaseMapping

HANDLE_URL = "https://biblioteca-repositorio.clacso.edu.ar/handle/CLACSO"
PDF_PART_URL = "https://biblioteca-repositorio.clacso.edu.ar"

class CLACSOMapping(BaseMapping):

    def __init__(self, clacso_record, namespaces):
        self.record = self._map_to_record(clacso_record, namespaces)

    def _map_to_record(self, clacso_record, namespaces):
        return Record(
            uuid=uuid4(),
            frbr_status=FRBRStatus.TODO.value,
            cluster_status=False,
            source=Source.CLACSO.value,
            source_id=self.create_source_id(clacso_record, namespaces),
            title=clacso_record.xpath('./dc:title/text()', namespaces=namespaces)[0],
            authors=self.create_authors(clacso_record, namespaces),
            medium=self.create_medium(clacso_record, namespaces),
            identifiers=self.create_identifiers(clacso_record, namespaces),
            has_part=self.create_has_part(clacso_record, namespaces),
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
                source_id = f'{Source.CLACSO.value}|{id}'
                return source_id

    def create_medium(self, record, namespaces):
        type_list = ['book', 'bookpart', 'part', 'chapter', 'bibliography', 'appendix', 'index',
                    'foreword', 'afterword', 'review', 'article', 'introduction']
        for medium in record.xpath('./dc:type/text()', namespaces=namespaces):
            if '/' in medium:
                medium_value = medium.split('/')[-1]
                if medium_value.lower() in type_list:
                    medium_value = medium_value.lower()
                    return medium_value
            elif '/' not in medium and medium.lower() in type_list:
                medium_value = medium
                return medium_value

    def create_identifiers(self, record, namespaces):
        identifier_array = [identifier for identifier in record.xpath('./dc:identifier/text()', namespaces=namespaces)]
        if identifier_array:
            identifier_array = list(map(lambda id: self.format_identifier(id, 'clacso'), identifier_array))
            return identifier_array

    def create_dates(self, record, namespaces):
        year_list = [date.split('-')[0] if '-' in date else date for date in record.xpath('./dc:date/text()', namespaces=namespaces)]
        date_issued = [f'{min(year_list)}|issued']
        return date_issued

    def create_has_part(self, record, namespaces):
            has_part_array = []
            has_part_urls = [has_part for has_part in record.xpath('./dc:identifier/text()', namespaces=namespaces) if 'http' in has_part]
            for url in has_part_urls:
                if HANDLE_URL in url or ("view" in url):
                    response = requests.get(url)
                    
                    clacso_page = BeautifulSoup(response.text, 'html.parser')
                    
                    links = clacso_page.find_all('a')
                    
                    for link in links:
                        if ('.pdf' in link.get('href', [])):
                            pdf_link = link.get('href')
                            if 'bitstream/CLACSO' in pdf_link:
                                response = requests.get(f'{PDF_PART_URL}{pdf_link}')
                            else:
                                response = requests.get(link.get('href'))
                            if response.status_code == 200:
                                pdf_part = Part(index=1, 
                                                url=f'{PDF_PART_URL}{pdf_link}',
                                                source=Source.CLACSO.value,
                                                file_type='application/pdf',
                                                flags=json.dumps(dataclasses.asdict(FileFlags(download=True))))
                                has_part_array.append(pdf_part.to_string())
                                return has_part_array
                            
    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass
