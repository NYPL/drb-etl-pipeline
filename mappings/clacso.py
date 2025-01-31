import re
import requests
from bs4 import BeautifulSoup

from mappings.xml import XMLMapping

class CLACSOMapping(XMLMapping):

    HANDLE_URL = "https://biblioteca-repositorio.clacso.edu.ar/handle/CLACSO"

    
    def __init__(self, source, namespace, constants):
        super(CLACSOMapping, self).__init__(source, namespace, constants)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'title': ('./dc:title/text()', '{0}'),
            'authors': [('./dc:creator/text()', '{0}|||true')],
            'abstract': ('./dc:description/text()', '{0}'),
            'dates': [
                (
                    [
                        './dc:date/text()',
                    ],
                    '{0}'
                )
            ],
            'identifiers': [
                ('./dc:identifier/text()', '{0}'),
            ],
            'medium' : [
                ('./dc:type/text()', '{0}')
            ],
            'has_part': [(
                './dc:identifier/text()',
                '1|{0}|clacso|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}'
            )]
        }

    def applyFormatting(self):
        self.record.source = 'clacso'
        if self.record.identifiers:
            self.record.identifiers = list(map(lambda x: self.format_identifier(x, self.record.source), self.record.identifiers))
        self.format_source_id()
        self.format_medium()
        self.format_dates()
        self.format_has_part()

    def format_source_id(self):
        for identifier in self.record.identifiers:
            if self.HANDLE_URL in identifier:
                id = identifier.split('/')[-1]
                self.record.source_id = f'{self.record.source}|{id}'
                return

    def format_medium(self):
        if self.record.medium:
            type_list = ['book', 'bookpart', 'part', 'chapter', 'bibliography', 'appendix', 'index',
                    'foreword', 'afterword', 'review', 'article', 'introduction']
            for medium in self.record.medium:
                if '/' in medium:
                    medium_value = medium.split('/')[-1]
                    if medium_value.lower() in type_list:
                        self.record.medium = medium_value.lower()
                        break
                elif '/' not in medium and medium.lower() in type_list:
                    medium_value = medium
                    self.record.medium = medium_value.lower()
                    break
        else:
            self.record.medium = ''

    def format_dates(self):
        if self.record.dates:
            year_list = [date.split('-')[0] if '-' in date else date for date in self.record.dates]
        self.record.dates = [f'{min(year_list)}|issued']

    def format_has_part(self):
        if self.record.has_part:
            clean_has_part = [has_part for has_part in self.record.has_part if 'http' in has_part]
            for has_part in clean_has_part:
                has_part_url = has_part.split('|')[1]
                if self.HANDLE_URL in has_part_url or ("view" in has_part_url):
                    response = requests.get(has_part_url)
                    
                    clacso_page = BeautifulSoup(response.text, 'html.parser')
                    
                    links = clacso_page.find_all('a')
                    
                    for link in links:
                        if ('.pdf' in link.get('href', [])):
                            pdf_link = link.get('href')
                            if 'bitstream/CLACSO' in pdf_link:
                                response = requests.get(f'{self.HANDLE_URL}{pdf_link}')
                            else:
                                response = requests.get(link.get('href'))
                            if response.status_code == 200:
                                has_part = (f'1|{self.HANDLE_URL}{pdf_link}|clacso|application/pdf|{{"reader": false, "download": true, "catalog": false, "embed": true}}')
                                clean_has_part.append(has_part)
                                self.record.has_part = clean_has_part
                                break
