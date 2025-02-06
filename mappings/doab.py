import re

from mappings.xml import XMLMapping

from datetime import datetime, timezone
from uuid import uuid4
import json
import dataclasses

from model import FileFlags, FRBRStatus, Part, Record, Source
from .base_mapping import BaseMapping
from .xml import _get_field_data_list

DOI_REGEX = r'doabooks.org\/handle\/([0-9]+\.[0-9]+\.[0-9]+\/[0-9]+)'
    
def map_doab_record(doab_record, namespaces) -> Record:
    identifiers, source_id = _get_identifers(doab_record, namespaces=namespaces)

    if identifiers is None or len(identifiers) == 0:
        return None

    authors = doab_record.xpath('./datacite:creator/text()', namespaces=namespaces)
    title = doab_record.xpath('./dc:title/text()', namespaces=namespaces)
    relations = doab_record.xpath('./dc:relation/text()', namespaces=namespaces)
    publishers = doab_record.xpath('./dc:publisher/text()', namespaces=namespaces)
    languages = doab_record.xpath('./dc:language/text()', namespaces=namespaces)
    extents = doab_record.xpath('./oapen:pages/text()', namespaces=namespaces)
    subjects = doab_record.xpath('./datacite:subject/text()', namespaces=namespaces)
    
    return Record(
        uuid=uuid4(),
        frbr_status=FRBRStatus.TODO.value,
        cluster_status=False,
        source=Source.DOAB.value,
        source_id=source_id,
        identifiers= identifiers,
        authors=[f"{author}|||true" for author in authors],
        contributors=_get_contributors(doab_record, namespaces=namespaces),
        title=title[0] if len(title) > 0 else None,
        is_part_of=[f"{part}||series" for part in relations],
        publisher=[f"{publisher}||" for publisher in publishers],
        spatial=doab_record.xpath('./oapen:placepublication/text()', namespaces=namespaces),
        dates=_get_dates(doab_record, namespaces=namespaces),
        languages=[f"||{language}" for language in languages],
        extent=[f"{extent} pages" for extent in extents],
        abstract=doab_record.xpath('./dc:description/text()', namespaces=namespaces),
        subjects=[f"{subject}||" for subject in subjects],
        has_part=_get_has_part(doab_record, namespaces),
        rights=_get_rights(doab_record, namespaces=namespaces),
        date_created=datetime.now(timezone.utc).replace(tzinfo=None),
        date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
    )

def _get_datacite_data(record, namespaces, text_xpath, type_xpath, format_string):
    text_data = record.xpath(text_xpath, namespaces=namespaces)
    type_data = record.xpath(type_xpath, namespaces=namespaces)

    if not text_data or not type_data:
        return None

    data_tuples = _get_field_data_list([text_data, type_data])

    return [format_string.format(item[0], item[1]) for item in data_tuples]

def _get_identifers(record, namespaces):
    dc_ids = record.xpath('./dc:identifier/text()', namespaces=namespaces)
    datacite_ids = record.xpath('./datacite:identifier/text()', namespaces=namespaces)
    datacite_alt_ids = _get_datacite_data(record, namespaces, './datacite:alternateIdentifier/text()', './datacite:alternateIdentifier/@type', "{}|{}")

    ids = [f"{id}|doab" for id in dc_ids + datacite_ids]

    all_identifiers = ids + datacite_ids

    if datacite_alt_ids:
        all_identifiers.extend(datacite_alt_ids)

    new_ids = []
    source_id = None

    for id in all_identifiers:
        try:
            value, auth = id.split('|')
        except ValueError:
            continue

        if value.startswith('http'):
            doab_doi_group = re.search(DOI_REGEX, value)
            if doab_doi_group:
                value = doab_doi_group.group(1)
                source_id = value
            else:
                continue

        new_ids.append(f"{value}|{auth.lower()}")

    return new_ids, source_id

def _get_contributors(record, namespaces):
    return _get_datacite_data(record, namespaces, './datacite:contributor/text()', './datacite:contributor/@type', "{}|||{}")

def _get_dates(record, namespaces):
    return _get_datacite_data(record, namespaces, './datacite:date/text()', './datacite:date/@type', "{}|||{}")

def _get_has_part(record, namespaces):
    dc_ids = record.xpath('./dc:identifier/text()', namespaces=namespaces)
    if not dc_ids:
        return None

    html_parts = [
        Part(
            index=1,
            url=dc_id,
            source=Source.DOAB.value,
            file_type='text/html',
            flags=json.dumps(dataclasses.asdict(FileFlags(embed=True)))
        ).to_string()
        for dc_id in dc_ids if "http" in dc_id
    ]
    
    return html_parts 

def _format_rights_data(uri_list, text_list):
    rights = []
    rights_tuple_list = _get_field_data_list([uri_list, text_list])
    for item in rights_tuple_list:
        right_str = f"doab|{item[0]}||{item[1]}"
        formatted_right = [d.strip() for d in right_str.split('|')]
        rights.append('|'.join(formatted_right))
    return rights

def _get_rights(record, namespaces):
    license_condition_uris = record.xpath('./oaire:licenseCondition/@uri', namespaces=namespaces)
    license_conditions_text = record.xpath('./oaire:licenseCondition/text()', namespaces=namespaces)

    rights_uris = record.xpath('./datacite:rights/@uri', namespaces=namespaces)
    rights_text = record.xpath('./datacite:rights/text()', namespaces=namespaces)

    if license_condition_uris and rights_uris:
        return None

    rights = []

    if license_condition_uris:
        rights.extend(_format_rights_data(license_condition_uris, license_conditions_text))

    if rights_uris:
        rights.extend(_format_rights_data(rights_uris, rights_text))

    return rights

class DOABMapping(XMLMapping):
    DOI_REGEX = r'doabooks.org\/handle\/([0-9]+\.[0-9]+\.[0-9]+\/[0-9]+)'

    def __init__(self, source, namespace, constants):
        super(DOABMapping, self).__init__(source, namespace, constants)
        self.mapping = self.createMapping()
    
    def createMapping(self):
        return {
            'identifiers': [
                ('./dc:identifier/text()', '{0}|doab'),
                ('./datacite:identifier/text()', '{0}|doab'),
                (
                    [
                        './datacite:alternateIdentifier/text()',
                        './datacite:alternateIdentifier/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'authors': [('./datacite:creator/text()', '{0}|||true')],
            'contributors': [(
                [
                    './datacite:contributor/text()',
                    './datacite:contributor/@type'
                ],
                '{0}|||{1}'
            )],
            'title': ('./datacite:title/text()', '{0}'),
            'is_part_of': [('./dc:relation/text()', '{0}||series')],
            'publisher': [('./dc:publisher/text()', '{0}||')],
            'spatial': ('./oapen:placepublication/text()', '{0}'),
            'dates': [
                (
                    [
                        './datacite:date/text()',
                        './datacite:date/@type'
                    ],
                    '{0}|{1}'
                )
            ],
            'languages': [('./dc:language/text()', '||{0}')],
            'extent': ('./oapen:pages/text()', '{0} pages'),
            'abstract': ('./dc:description/text()', '{0}'),
            'subjects': [('./datacite:subject/text()', '{0}||')],
            'has_part': [(
                './dc:identifier/text()',
                '1|{0}|doab|text/html|{{"reader": false, "download": false, "catalog": false, "embed": true}}'
            )],
            'rights': [
                (
                    [
                        './oaire:licenseCondition/@uri',
                        './oaire:licenseCondition/text()'
                    ],
                    'doab|{0}||{1}|'
                ),
                (
                    [
                        './datacite:rights/@uri',
                        './datacite:rights/text()'
                    ],
                    'doab|{0}||{1}|'
                )
            ]
        }

    def applyFormatting(self):
        # Set Identifiers
        self.record.source = 'doab'
        self.record.identifiers = self.parseIdentifiers()

        # Clean up subjects
        self.record.subjects = list(filter(lambda x: x[:3] != 'bic', self.record.subjects))

        # Clean up rights statements
        self.record.rights = self.parseRights()

        # Clean up links
        self.record.has_part = self.parseLinks()

        if self.record.source_id is None or len(self.record.identifiers) < 1:
            self.raiseMappingError('Malformed DOAB record')

    def parseIdentifiers(self):
        outIDs = []

        for iden in self.record.identifiers:
            try:
                value, auth = iden.split('|')
            except ValueError:
                continue

            if value[:4] == 'http':
                doabDOIGroup = re.search(self.DOI_REGEX, value)

                if doabDOIGroup:
                    value = doabDOIGroup.group(1)
                    self.record.source_id = value
                else:
                    continue

            outIDs.append('{}|{}'.format(value, auth.lower()))

        return outIDs

    def parseRights(self):
        for rightsObj in self.record.rights:
            rightsData = [d.strip() for d in list(rightsObj.split('|'))]
            if rightsData[1] == '': continue

            return '|'.join(rightsData)

        return None

    def parseLinks(self):
        outLinks = []
        
        for link in self.record.has_part:
            _, uri, *_ = link.split('|')

            if uri[:4] != 'http': continue

            outLinks.append(link)
        
        return outLinks
