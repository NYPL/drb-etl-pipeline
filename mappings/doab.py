import re

from mappings.xml import XMLMapping

from datetime import datetime, timezone
from uuid import uuid4
import json
import dataclasses

from model import FileFlags, FRBRStatus, Part, Record, Source
from .base_mapping import BaseMapping


class DOABMapping(BaseMapping):
    DOI_REGEX = r'doabooks.org\/handle\/([0-9]+\.[0-9]+\.[0-9]+\/[0-9]+)'

    def __init__(self, doab_record, namespaces):
        self.record = self.map_doab_record(doab_record, namespaces)
    
    def map_doab_record(self, doab_record, namespaces) -> Record:
        identifiers, source_id = self._get_identifers(doab_record, namespaces=namespaces)

        if identifiers is None or len(identifiers) == 0:
            return None

        title = doab_record.xpath('./dc:title/text()', namespaces=namespaces) + doab_record.xpath('./datacite:creator/text()', namespaces=namespaces)
        relations = doab_record.xpath('./dc:relation/text()', namespaces=namespaces)
        publishers = doab_record.xpath('./dc:publisher/text()', namespaces=namespaces)
        languages = doab_record.xpath('./dc:language/text()', namespaces=namespaces)
        extents = doab_record.xpath('./oapen:pages/text()', namespaces=namespaces)
        
        return Record(
            uuid=uuid4(),
            frbr_status=FRBRStatus.TODO.value,
            cluster_status=False,
            source=Source.DOAB.value,
            source_id=source_id,
            identifiers= identifiers,
            authors=self._get_authors(doab_record, namespaces=namespaces),
            contributors=self._get_contributors(doab_record, namespaces=namespaces),
            title=title[0] if len(title) > 0 else None,
            is_part_of=[f"{part}||series" for part in relations],
            publisher=[f"{publisher}||" for publisher in publishers],
            spatial=doab_record.xpath('./oapen:placepublication/text()', namespaces=namespaces),
            dates=self._get_dates(doab_record, namespaces=namespaces),
            languages=[f"||{language}" for language in languages],
            extent=[f"{extent} pages" for extent in extents],
            abstract=doab_record.xpath('./dc:description/text()', namespaces=namespaces),
            subjects=self._get_subjects(doab_record, namespaces=namespaces),
            has_part=self._get_has_part(doab_record, namespaces),
            rights=self._get_rights(doab_record, namespaces=namespaces),
            date_created=datetime.now(timezone.utc).replace(tzinfo=None),
            date_modified=datetime.now(timezone.utc).replace(tzinfo=None)
        )

    def _get_text_type_data(self,record, namespaces, field_xpath, format_string):
        field_data = record.xpath(field_xpath, namespaces=namespaces)

        if not field_data:
            return None

        data_tuples = [
            (item.text, item.get("type") or '')
            for item in field_data
        ]
        
        return [format_string.format(item[0], item[1]) for item in data_tuples]

    def _get_authors(self, record, namespaces):
        datacite_authors = record.xpath('./datacite:creator/text()', namespaces=namespaces)
        dc_authors = record.xpath('./dc:creator/text()', namespaces=namespaces)

        authors = datacite_authors or dc_authors

        return [f"{author}|||true" for author in authors]

    def _get_identifers(self, record, namespaces):
        dc_ids = record.xpath('./dc:identifier/text()', namespaces=namespaces)
        datacite_ids = record.xpath('./datacite:identifier/text()', namespaces=namespaces)
        
        datacite_alt_ids = self._get_text_type_data(record, namespaces, './datacite:alternateIdentifier', "{}|{}")
        dc_alt_ids = self._get_text_type_data(record, namespaces, './dc:alternateIdentifier', "{}|{}")

        ids = [f"{id}|doab" for id in dc_ids + datacite_ids]

        if datacite_alt_ids:
            ids.extend(datacite_alt_ids)

        if dc_alt_ids:
            ids.extend(dc_alt_ids)

        new_ids = []
        source_id = None

        for id in ids:
            try:
                value, auth = id.split('|')
            except ValueError:
                continue

            if value.startswith('http'):
                doab_doi_group = re.search(self.DOI_REGEX, value)
                if doab_doi_group:
                    value = doab_doi_group.group(1)
                    source_id = value
                else:
                    continue

            new_ids.append(f"{value}|{auth.lower()}")

        return new_ids, source_id

    def _get_contributors(self, record, namespaces):
        return self._get_text_type_data(record, namespaces, './datacite:contributor', "{}|||{}")

    def _get_dates(self, record, namespaces):
        datacite_dates = self._get_text_type_data(record, namespaces, './datacite:date', "{}|||{}")
        dc_dates = self._get_text_type_data(record, namespaces, './dc:date', "{}|||{}")

        return datacite_dates or dc_dates

    def _get_subjects(self, record, namespaces):
        datacite_subjects = record.xpath('./datacite:subject/text()', namespaces=namespaces)
        dc_subjects = record.xpath('./dc:subject/text()', namespaces=namespaces)
        
        subjects = datacite_subjects or dc_subjects

        return [f"{subject}||" for subject in subjects if subject[:3] != 'bic']

    def _get_has_part(self, record, namespaces):
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

    def _get_uri_text_data(self, record, namespaces, field_xpath, format_string):
        field_data = record.xpath(field_xpath, namespaces=namespaces)

        if not field_data:
            return []

        data_tuples = [
            (item.get("uri") or '', item.text.strip())
            for item in field_data
        ]
        
        return [format_string.format(item[0], item[1]) for item in data_tuples]

    def _get_rights(self, record, namespaces):
        license_conditions = self._get_uri_text_data(record, namespaces, './oaire:licenseCondition', "doab|{}||{}")
        
        datacite_rights = self._get_uri_text_data(record, namespaces, './datacite:rights', "doab|{}||{}")

        dc_rights = self._get_uri_text_data(record, namespaces, './dc:rights', "doab|{}||{}")

        if not license_conditions and not datacite_rights and not dc_rights:
            return None

        return license_conditions + datacite_rights + dc_rights

    def createMapping(self):
        pass

    def applyFormatting(self):
        pass

    def applyMapping(self):
        pass
