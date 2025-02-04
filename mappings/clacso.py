import re
import requests
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from uuid import uuid4
from lxml import etree

from model import Record

# class CLACSOMapping(XMLMapping):

HANDLE_URL = "https://biblioteca-repositorio.clacso.edu.ar/handle/CLACSO"
PDF_PART_URL = "https://biblioteca-repositorio.clacso.edu.ar"

    
    # def __init__(, clacso_record, namespace, constants):
    #     super(CLACSOMapping, ).__init__(clacso_record, namespace, constants)
    #     record = _map_to_record(clacso_record)
    #     #mapping = createMapping()

    # def createMapping():

    #     mapping = {
    #         'title': ('./dc:title/text()', '{0}'),
    #         'authors': [('./dc:creator/text()', '{0}|||true')],
    #         'abstract': ('./dc:description/text()', '{0}'),
    #         'dates': [
    #             (
    #                 [
    #                     './dc:date/text()',
    #                 ],
    #                 '{0}'
    #             )
    #         ],
    #         'identifiers': [
    #             ('./dc:identifier/text()', '{0}'),
    #         ],
    #         'medium' : [
    #             ('./dc:type/text()', '{0}')
    #         ],
    #         'has_part': [(
    #             './dc:identifier/text()',
    #             '1|{0}|clacso|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}'
    #         )]
    #     }

def _map_to_record(clacso_record, namespaces):
    mapped_record = Record(
        uuid=uuid4(),
        frbr_status='to_do',
        cluster_status=False,
        source='clacso',
        source_id=create_source_id(clacso_record, namespaces),
        title=clacso_record.xpath('./dc:title/text()', namespaces=namespaces,)[0],
        authors=create_authors(clacso_record, namespaces),
        medium=create_medium(clacso_record, namespaces),
        #identifiers=create_identifiers(clacso_record, namespaces)
        has_part=create_has_part(clacso_record, namespaces),
        dates=create_dates(clacso_record, namespaces),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )
    return mapped_record

def create_authors(record, namespaces):
    author_list = []
    for author in record.xpath('./dc:creator/text()', namespaces=namespaces):
        author_list.append(f'{author}|||true')
    return author_list

def create_source_id(record, namespaces):
    for identifier in record.xpath('./dc:identifier/text()', namespaces=namespaces):
        if HANDLE_URL in identifier:
            id = identifier.split('/')[-1]
            source_id = f'{identifier}|{id}'
            return source_id

def create_medium(record, namespaces):
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

def create_identifers(record, namespaces):
    pass
    # if record.identifiers:
    #     record.identifiers = list(map(lambda id: format_identifier(id, record.source), record.identifiers))
    #     return

def create_dates(record, namespaces):
    year_list = [date.split('-')[0] if '-' in date else date for date in record.xpath('./dc:date/text()', namespaces=namespaces)]
    date_issued = [f'{min(year_list)}|issued']
    return date_issued

def create_has_part(record, namespaces):
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
                            has_part_format = (f'1|{PDF_PART_URL}{pdf_link}|clacso|application/pdf|{{"reader": false, "download": true, "catalog": false, "embed": true}}')
                            has_part_array.append(has_part_format)
                            return has_part_array

def format_identifier(identifier, source):
    identifier_type_dict = {8: 'issn', 10: 'isbn', 13: 'isbn'}
    numeric_identifier = [char for char in identifier if char.isdigit()]
    return f'{identifier}|{identifier_type_dict.get(len(numeric_identifier), source)}'
