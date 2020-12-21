from collections import Counter, defaultdict
from datetime import datetime, timedelta, date
import json
from math import floor
import pycountry
import re
from uuid import uuid4

from model import Base, Record, Work, Edition, Item, Identifier, Link, Rights


class SFRRecordManager:
    TITLE_STOPWORDS = {
        'eng': ['a', 'an', 'the'],
        'fra': ['le', 'la', 'les', 'l', 'un', 'une'],
        'esp': ['el', 'la', 'los', 'las', 'un', 'una']
    }

    def __init__(self, session):
        self.session = session
        self.work = Work(uuid=uuid4(), editions=[])

    def mergeRecords(self):
        existingIDs = {}
        for edition in self.work.editions:
            matchedEditions = self.session.query(Edition)\
                .filter(Edition.dcdw_uuids.overlap(edition.dcdw_uuids))\
                .all()

            if matchedEditions:
                useEdition = matchedEditions[0]
                self.work.id = useEdition.work_id
                edition.id = useEdition.id
                for otherEd in matchedEditions[1:]:
                    self.session.delete(otherEd.work)
                    self.session.delete(otherEd)
                
            edition.identifiers = self.dedupeIdentifiers(edition.identifiers, existingIDs)

            for item in edition.items:
                item.identifiers = self.dedupeIdentifiers(item.identifiers, existingIDs)
                item.links = self.dedupeLinks(item.links)

        self.work.identifiers = self.dedupeIdentifiers(self.work.identifiers, existingIDs)

        self.session.merge(self.work)

    def dedupeIdentifiers(self, identifiers, existingIDs):
        cleanIdentifiers = set()
        for i in range(len(identifiers)):
            idTuple = (identifiers[i].identifier, identifiers[i].authority)
            if (idTuple) in existingIDs.keys():
                cleanIdentifiers.add(existingIDs[idTuple])
            else:
                matchedID = self.session.query(Identifier)\
                    .filter(Identifier.identifier == idTuple[0])\
                    .filter(Identifier.authority == idTuple[1])\
                    .one_or_none()
                if matchedID:
                    identifiers[i].id = matchedID.id

                cleanIdentifiers.add(identifiers[i])
                existingIDs[idTuple] = identifiers[i]

        return list(cleanIdentifiers)

    def dedupeLinks(self, links):
        cleanLinks = set()
        for link in links:
            matchedLink = self.session.query(Link)\
                .filter(Link.url == link.url)\
                .first()
            if matchedLink:
                link.id = matchedLink.id
                cleanLinks.add(link)
            else:
                cleanLinks.add(link)
        
        return list(cleanLinks)

    def buildEditionStructure(self, records, editions):
        editionRecs = {}

        for editionTuple in editions:
            edYear, recs = editionTuple
            editionRecs[edYear] = list(filter(None, [
                r if r.uuid in recs else None for r in records
            ]))
        
        return editionRecs

    def buildWork(self, records, editions):
        editionRecs = self.buildEditionStructure(records, editions)
        
        workData = SFRRecordManager.createEmptyWorkRecord()
        
        for pubYear, instances in editionRecs.items():
            self.buildEdition(workData, pubYear, instances)
        
        return workData
    
    def buildEdition(self, workData, pubYear, instances):
        editionData = SFRRecordManager.createEmptyEditionRecord()

        # Publication Year
        editionData['publication_date'] = pubYear

        for rec in instances:
            self.parseInstance(workData, editionData, rec)

        workData['editions'].append(editionData)
    
    def parseInstance(self, workData, editionData, rec):
        # Title Fields
        workData['title'][rec.title] += 1
        editionData['title'][rec.title] += 1
        if rec.alternative:
            for alt in rec.alternative:
                workData['alt_titles'][alt] += 1
                editionData['alt_titles'][alt] += 1

        # Medium
        workData['medium'][rec.medium] += 1

        # is_part_of (Series and Volume)
        if rec.is_part_of:
            for partOf in rec.is_part_of:
                if partOf[-6:] == 'series':
                    workData['series_data'][partOf] += 1
                elif partOf[-6:] == 'volume':
                    editionData['volume_data'][partOf] += 1
        
        # Edition
        if rec.has_version:
            editionData['edition_data'][rec.has_version] += 1

        # Identifiers
        workData['identifiers'].update(rec.identifiers)
        editionData['identifiers'].update(rec.identifiers)
        
        # Authors
        workData['authors'].update(rec.authors)

        # Publishers
        if rec.publisher:
            editionData['publishers'].add(rec.publisher)
        
        # Publication_place
        editionData['publication_place'][rec.spatial] += 1
        
        # Contributors
        itemContributors = set()
        for contrib in rec.contributors:
            try:
                _, _, _, role = tuple(contrib.split('|'))
            except ValueError:
                _, role = tuple(contrib.split('|'))
            if role in ['publisher', 'manufacturer', 'distributor', 'printer']:
                editionData['contributors'].add(contrib)
            elif role in ['provider', 'repository', 'digitizer', 'responsible']:
                itemContributors.add(contrib)
            else:
                workData['contributors'].add(contrib)

        # Subjects
        if rec.subjects:
            workData['subjects'].update(rec.subjects)
        
        # Dates
        editionData['dates'].update(rec.dates)

        # Languages
        workData['languages'].update(rec.languages)
        editionData['languages'].update(rec.languages)

        # Summary/TOC/Extent
        editionData['summary'][rec.abstract] += 1
        editionData['table_of_contents'][rec.table_of_contents] += 1
        editionData['extent'][rec.extent] += 1

        # Measurements
        if rec.requires:
            for measure in rec.requires:
                _, measurement = tuple(measure.split('|'))
                if measurement == 'government_doc':
                    workData['measurements'].add(measure)
                else:
                    editionData['measurements'].add(measure)
        
        # Item Records
        if rec.has_part:
            self.buildItems(editionData, rec, itemContributors)

        editionData['items'] = list(filter(None, editionData['items']))

        editionData['dcdw_uuids'].append(rec.uuid.hex)

    def buildItems(self, editionData, rec, itemContributors):
        startPos = len(editionData['items']) - 1
        editionData['items'].extend([None] * len(rec.has_part))

        for item in rec.has_part:
            no, uri, source, linkType, flags = tuple(item.split('|'))

            try:
                linkFlags = json.loads(flags)
                linkFlags = linkFlags if isinstance(linkFlags, dict) else {}
            except json.decoder.JSONDecodeError:
                linkFlags = {}

            if linkFlags.get('cover', False) is True:
                editionData['links'].append('{}|{}|{}'.format(uri, linkType, flags))

                continue

            itemPos = startPos + int(no)
            if editionData['items'][itemPos] is None:
                editionData['items'][itemPos] = {
                    'links': [],
                    'identifiers': set(),
                    'contributors': set()
                }
            editionData['items'][itemPos] = {
                **editionData['items'][itemPos],
                **{
                    'source': source,
                    'content_type': 'ebook',
                    'modified': rec.date_submitted,
                }
            }

            editionData['items'][itemPos]['links'].append('{}|{}|{}'.format(uri, linkType, flags))

            editionData['items'][itemPos]['identifiers'].update([
                i for i in list(filter(lambda x: re.search(r'\|(?!isbn|issn|oclc|lccn|owi|ddc|lcc|nypl).*$', x), rec.identifiers))
            ])

            editionData['items'][itemPos]['contributors'].update(itemContributors)

            if rec.coverage and len(rec.coverage) > 0:
                for location in rec.coverage:
                    locationCode, locationName, itemNo = tuple(location.split('|'))
                    if itemNo == no:
                        editionData['items'][itemPos]['physical_location'] = {
                            'code': locationCode,
                            'name': locationName
                        }
                        break
        
    def saveWork(self, workData):
        # Set Titles
        self.work.title = workData['title'].most_common(1)[0][0]
        if len(workData['sub_title']):
            self.work.sub_title = workData['sub_title'].most_common(1)[0][0]
        self.work.alt_titles = [t[0] for t in workData['alt_titles'].most_common()]
        
        # Set Agents
        self.work.authors = self.agentParser(workData['authors'], ['name', 'viaf', 'lcnaf', 'primary'])
        self.work.contributors = self.agentParser(workData['contributors'], ['name', 'viaf', 'lcnaf', 'role'])

        # Set Identifiers
        self.work.identifiers = SFRRecordManager.setPipeDelimitedData(
            workData['identifiers'], ['identifier', 'authority'], Identifier
        )

        # Set Subjects
        self.work.subjects = SFRRecordManager.setPipeDelimitedData(
            workData['subjects'], ['heading', 'authority', 'controlNo']
        )

        # Set Measurements 
        self.work.measurements = SFRRecordManager.setPipeDelimitedData(workData['measurements'], ['value', 'type'])

        # Set Languages
        self.work.languages = SFRRecordManager.setPipeDelimitedData(
            workData['languages'], ['language', 'iso_2', 'iso_3'], dParser=SFRRecordManager.getLanguage
        )

        # Set Medium
        self.work.medium = workData['medium'].most_common(1)[0][0]

        # Set Series
        if workData['series_data']:
            series, seriesPos = tuple(workData['series_data'].most_common(1)[0][0].split('|'))
            self.work.series = series
            self.work.series_position = seriesPos

        # Add Editions
        for ed in workData['editions']:
            self.work.editions.append(self.saveEdition(ed))
        
        # Set Sort Title
        self.setSortTitle()

    def saveEdition(self, edition):
        newEd = Edition(items=[], links=[])

        # Set Titles
        newEd.title = edition['title'].most_common(1)[0][0]
        if len(edition['sub_title']):
            newEd.sub_title = edition['sub_title'].most_common(1)[0][0]
        newEd.alt_titles = [t[0] for t in edition['alt_titles'].most_common()]

        # Set Publication Data
        try:
            pubYear = floor(edition['publication_date'])
            newEd.publication_date = date(year=pubYear, month=1, day=1)
        except (ValueError, TypeError) as err:
            pass
        newEd.publication_place = edition['publication_place'].most_common(1)[0][0]

        # Set Abstract Data
        newEd.table_of_contents = edition['table_of_contents'].most_common(1)[0][0]
        newEd.extent = edition['extent'].most_common(1)[0][0]
        newEd.summary = edition['summary'].most_common(1)[0][0]

        # Set Edition Data
        if len(edition['edition_data']):
            print(edition['edition_data'])
            editionStmt, editionNo = tuple(edition['edition_data'].most_common(1)[0][0].split('|'))
            newEd.edition_statement = editionStmt
            newEd.edition = editionNo

        # Set Volume Data
        if len(edition['volume_data']):
            volume, volumeNo, _ = tuple(edition['volume_data'].most_common(1)[0][0].split('|'))
            newEd.volume = '{}, {}'.format(volume, volumeNo)
        
        # Set Agents
        newEd.contributors = self.agentParser(edition['contributors'], ['name', 'viaf', 'lcnaf', 'role'])
        newEd.publishers = self.agentParser(edition['publishers'], ['name', 'viaf', 'lcnaf'])

        # Set Identifiers
        newEd.identifiers = SFRRecordManager.setPipeDelimitedData(
            edition['identifiers'], ['identifier', 'authority'], Identifier
        )

        # Set Languages
        newEd.languages = SFRRecordManager.setPipeDelimitedData(
            edition['languages'], ['language', 'iso_2', 'iso_3'], dParser=SFRRecordManager.getLanguage
        )

        # Set Measurements 
        newEd.measurements = SFRRecordManager.setPipeDelimitedData(edition['measurements'], ['value', 'type'])

        # Set Dates
        newEd.dates = SFRRecordManager.setPipeDelimitedData(edition['dates'], ['date', 'type'])

        # Set Links
        newEd.links = SFRRecordManager.setPipeDelimitedData(
            edition['links'], ['url', 'media_type', 'flags'], Link
        )

        # Add Items
        for item in edition['items']:
            newEd.items.append(self.saveItem(item))
        
        # Set DCDW UUIDs
        newEd.dcdw_uuids = list(edition['dcdw_uuids'])
        
        return newEd


    def saveItem(self, item):
        links = item.pop('links', [])
        identifiers = item.pop('identifiers', [])
        newItem = Item(**item)

        # Set Links
        newItem.links = SFRRecordManager.setPipeDelimitedData(
            links, ['url', 'media_type', 'flags'], Link
        )
        
        # Set Identifiers
        newItem.identifiers = SFRRecordManager.setPipeDelimitedData(
            identifiers, ['identifier', 'authority'], Identifier
        )

        # Set Contributors
        newItem.contributors = self.agentParser(item['contributors'], ['name', 'viaf', 'lcnaf', 'role'])

        return newItem

    @staticmethod
    def setPipeDelimitedData(data, fields, dType=None, dParser=None):
        return [
            SFRRecordManager.parseDelimitedEntry(d, fields, dType, dParser) for d in data
        ]

    @staticmethod
    def parseDelimitedEntry(dInst, fields, dType, dParser):
        dataEntry = dict(zip(fields, dInst.split('|')))
        if dParser is not None:
            dataEntry = dParser(dataEntry)
        if dType is None:
            return dataEntry

        return dType(**dataEntry)

    @staticmethod
    def getLanguage(langData):
        values = list(filter(lambda x: x != '', [v for _, v in langData.items()]))
        for v in values:
            for attr in ['alpha_2', 'alpha_3', 'name']:
                pyLang = pycountry.languages.get(**{attr: v})
                if pyLang is not None:
                    try:
                        iso2 = pyLang.alpha_2
                    except AttributeError:
                        iso2 = None
                    return {'language': pyLang.name, 'iso_2': iso2, 'iso_3': pyLang.alpha_3}

    def agentParser(self, agents, fields):
        outAgents = []
        for agent in agents:
            agentParts = agent.split('|')
            if len(agentParts) < len(fields):
                agentParts.insert(1, '')
                agentParts.insert(2, '')
            rec = dict(zip(fields, agentParts))

            if rec['name'] == '' and rec['viaf'] == '' and rec['lcnaf'] == '':
                continue
            
            for oa in outAgents:
                for checkField in ['name', 'viaf', 'lcnaf']:
                    if rec[checkField] and rec[checkField] != '' and rec[checkField] == oa[checkField]:
                        if oa['viaf'] == '':
                            oa['viaf'] = rec['viaf']

                        if oa['lcnaf'] == '':
                            oa['lcnaf'] = rec['lcnaf']

                        if 'role' in rec.keys():
                            oa['roles'].add(rec['role'])
                        break
                else:
                    continue
                break
            else:
                if 'role' in rec.keys():
                    rec['roles'] = set([rec['role']])
                    del rec['role']
                outAgents.append(rec)

        for ag in outAgents:
            if 'roles' in ag.keys():
                ag['roles'] = list(ag['roles'])

        return outAgents

    @staticmethod
    def createEmptyWorkRecord():
        return {
            'title': Counter(),
            'sub_title': Counter(),
            'alt_titles': Counter(),
            'medium': Counter(),
            'series_data': Counter(),
            'identifiers': set(),
            'authors': set(),
            'contributors': set(),
            'subjects': set(),
            'dates': set(),
            'languages': set(),
            'measurements': set(),
            'editions': [],
        }
    
    @staticmethod
    def createEmptyEditionRecord():
        return {
            'title': Counter(),
            'sub_title': Counter(),
            'alt_titles': Counter(),
            'edition_data': Counter(),
            'publication_place': Counter(),
            'publication_date': None, 
            'volume_data': Counter(),
            'table_of_contents': Counter(),
            'extent': Counter(),
            'summary': Counter(),
            'identifiers': set(),
            'publishers': set(),
            'contributors': set(),
            'dates': set(),
            'measurements': set(),
            'languages': set(),
            'items': [],
            'links': [],
            'dcdw_uuids': []
        }
    
    def setSortTitle(self):
        stops = [
            s for l in [l['iso_3'] if l else None for l in self.work.languages]
            for s in self.TITLE_STOPWORDS.get(l, [])
        ]

        tokens = re.split(r'\s+', self.work.title)

        self.work.sort_title = ' '.join(tokens[1:] if tokens[0].lower() in stops else tokens).lower()
