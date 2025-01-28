import re
import requests
from bs4 import BeautifulSoup

from mappings.xml import XMLMapping

class CLACSOMapping(XMLMapping):
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
        handle_url = "https://biblioteca-repositorio.clacso.edu.ar/handle/CLACSO"
        self.formatting_source_id(handle_url)
        self.formatting_medium()
        self.formatting_dates()
        self.formatting_identifiers()
        self.formatting_has_part(handle_url)

    def formatting_source_id(self, handle_url):
        for identifier in self.record.identifiers:
            if handle_url in identifier:
                id = identifier.split('/')[-1]
                self.record.source_id = f'{self.record.source}|{id}'
                break

    def formatting_medium(self):
        if self.record.medium:
            type_list = ['book', 'bookpart', 'part', 'chapter', 'bibliography', 'appendix', 'index',
                    'foreword', 'afterword', 'bibliography', 'review', 'article', 'introduction']
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

    def formatting_dates(self):
        if self.record.dates:
            year_list = []
            for date in self.record.dates:
                if '-' in date:
                    year_list.append(date.split('-')[0])
                else:
                    year_list.append(date)
        self.record.dates = [f'{min(year_list)}|issued']

    def formatting_identifiers(self):
        if self.record.identifiers:
            for index, identifier in enumerate(self.record.identifiers):
                count_digits = 0
                if '/' not in identifier:
                    for char in identifier:
                        if char.isdigit():
                            count_digits += 1
                    if count_digits == 8:
                        self.record.identifiers[index] = f'{identifier}|issn'
                    if count_digits == 10 or count_digits == 13:
                        self.record.identifiers[index] = f'{identifier}|isbn'
                else:
                    self.record.identifiers[index] = f'{identifier}|clacso'
                

    def formatting_has_part(self, handle_url):
        if self.record.has_part:
            clean_has_part = [has_part for has_part in self.record.has_part if 'http' in has_part]
            for has_part in clean_has_part:
                has_part_url = has_part.split('|')[1]
                if handle_url in has_part_url or ("view" in has_part_url):
                    response = requests.get(has_part_url)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    links = soup.find_all('a')
                    
                    for link in links:
                        if ('.pdf' in link.get('href', [])):
                            pdf_link = link.get('href')
                            if 'bitstream/CLACSO' in pdf_link:
                                response = requests.get(f'{handle_url}{pdf_link}')
                            else:
                                response = requests.get(link.get('href'))
                            if response.status_code == 200:
                                has_part = (f'1|{handle_url}{pdf_link}|clacso|application/pdf|{{"reader": false, "download": true, "catalog": false, "embed": true}}')
                                clean_has_part.append(has_part)
                                self.record.has_part = clean_has_part
                                break
