from collections import Counter, defaultdict
from datetime import date
import json
from Levenshtein import jaro_winkler
import pycountry
import re
from uuid import uuid4

from model import Work, Edition, Item, Identifier, Link, Rights


class SFRRecordManager:
    TITLE_STOPWORDS = {
        'eng': ['a', 'an', 'the'],
        'fra': ['le', 'la', 'les', 'l', 'un', 'une'],
        'esp': ['el', 'la', 'los', 'las', 'un', 'una']
    }

    def __init__(self, session, iso639):
        self.session = session
        self.iso639_2b = iso639['2b']
        self.work = Work(uuid=uuid4(), editions=[])

    def mergeRecords(self):
        existingIDs = {}
        uuidsToDelete = set()

        dcdwUUIDs = set()
        for edition in self.work.editions:
            dcdwUUIDs.union(edition.dcdw_uuids)

        matchedEditions = defaultdict(list)
        for matchedEdition in self.session.query(Edition)\
            .filter(Edition.dcdw_uuids.overlap(list(dcdwUUIDs))).all():
            for matchedUUID in matchedEdition.dcdw_uuids:
                matchedEditions[matchedUUID].append(matchedEdition)

        for edition in self.work.editions:
            existingEditions = []
            for dcdwUUID in edition.dcdw_uuids:
                existingEditions.extend(matchedEditions.get(dcdwUUID, []))

            if len(existingEditions) > 0:
                useEdition = existingEditions[0]
                self.work.id = useEdition.work_id
                edition.id = useEdition.id
                for otherEd in existingEditions[1:]:
                    self.session.delete(otherEd.work)
                    uuidsToDelete.add(otherEd.work.uuid)
                
            edition.identifiers = self.dedupeIdentifiers(edition.identifiers, existingIDs)

            for item in edition.items:
                item.identifiers = self.dedupeIdentifiers(item.identifiers, existingIDs)
                item.links = self.dedupeLinks(item.links)

        self.work.identifiers = self.dedupeIdentifiers(self.work.identifiers, existingIDs)

        self.work = self.session.merge(self.work)

        return uuidsToDelete

    def dedupeIdentifiers(self, identifiers, existingIDs):
        queryGroups = defaultdict(list)
        cleanIdentifiers = set()

        for iden in identifiers:
            if existingIDs.get((iden.authority, iden.identifier), None):
                cleanIdentifiers.add(existingIDs[(iden.authority, iden.identifier)])
                continue

            queryGroups[iden.authority].append(iden)

        for authority, identifiers in queryGroups.items():
            idenNos = {i.identifier: i for i in identifiers}

            for matchedID in self.session.query(Identifier)\
                .filter(Identifier.identifier.in_(idenNos.keys()))\
                .filter(Identifier.authority == authority)\
                .all():
                try:
                    newIden = idenNos[matchedID.identifier]
                    newIden.id = matchedID.id
                    cleanIdentifiers.add(newIden)
                    existingIDs[(newIden.authority, newIden.identifier)] = newIden
                    del idenNos[matchedID.identifier]
                except KeyError:
                    pass

            for _, newIden in idenNos.items():
                cleanIdentifiers.add(newIden)
                existingIDs[(newIden.authority, newIden.identifier)] = newIden

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
        editionRecs = [] 

        for editionTuple in editions:
            edYear, recs = editionTuple
            editionRecs.append((edYear, list(filter(None, [
                r if r.uuid in recs else None for r in records
            ]))))
        
        return editionRecs

    def buildWork(self, records, editions):
        editionRecs = self.buildEditionStructure(records, editions)
        
        workData = SFRRecordManager.createEmptyWorkRecord()
        
        for pubYear, instances in editionRecs:
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
            role = tuple(contrib.split('|'))[-1]

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
        editionData['dates'].update(self.normalizeDates(rec.dates))

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
                    'rights': rec.rights
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
        try:
            self.work.title = workData['title'].most_common(1)[0][0].strip(' .:/')
        except IndexError:
            self.work.title = ''

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
        self.subjectParser(workData['subjects'])
        
        # Set Measurements 
        self.work.measurements = SFRRecordManager.setPipeDelimitedData(workData['measurements'], ['value', 'type'])

        # Set Languages
        self.work.languages = SFRRecordManager.setPipeDelimitedData(
            workData['languages'], ['language', 'iso_2', 'iso_3'], dParser=self.getLanguage
        )

        # Set Medium
        try:
            self.work.medium = workData['medium'].most_common(1)[0][0]
        except IndexError:
            pass

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
        newEd.title = edition['title'].most_common(1)[0][0].strip(' .:/')
        if len(edition['sub_title']):
            newEd.sub_title = edition['sub_title'].most_common(1)[0][0]
        newEd.alt_titles = [t[0] for t in edition['alt_titles'].most_common()]

        # Set Publication Data
        pubYearGroup = re.search(r'([0-9]{4})', str(edition['publication_date']))
        if pubYearGroup:
            newEd.publication_date = date(year=int(pubYearGroup.group(1)), month=1, day=1)

        newEd.publication_place = edition['publication_place'].most_common(1)[0][0]

        # Set Abstract Data
        newEd.table_of_contents = edition['table_of_contents'].most_common(1)[0][0]
        newEd.extent = edition['extent'].most_common(1)[0][0]
        newEd.summary = edition['summary'].most_common(1)[0][0]

        # Set Edition Data
        if len(edition['edition_data']):
            editionStmt, editionNo = tuple(edition['edition_data'].most_common(1)[0][0].split('|'))
            newEd.edition_statement = editionStmt
            try:
                newEd.edition = int(editionNo)
            except ValueError:
                pass

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
            edition['languages'], ['language', 'iso_2', 'iso_3'], dParser=self.getLanguage
        )

        # Set Measurements 
        newEd.measurements = SFRRecordManager.setPipeDelimitedData(edition['measurements'], ['value', 'type'])

        # Set Dates
        newEd.dates = SFRRecordManager.setPipeDelimitedData(edition['dates'], ['date', 'type'])

        # Set Links
        newEd.links = SFRRecordManager.setPipeDelimitedData(
            edition['links'], ['url', 'media_type', 'flags'], Link, dParser=SFRRecordManager.parseLinkFlags
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
        rights = item.pop('rights', [])
        newItem = Item(**item)

        # Set Links
        newItem.links = SFRRecordManager.setPipeDelimitedData(
            links, ['url', 'media_type', 'flags'], Link, dParser=SFRRecordManager.parseLinkFlags
        )
        
        # Set Identifiers
        newItem.identifiers = SFRRecordManager.setPipeDelimitedData(
            identifiers, ['identifier', 'authority'], Identifier
        )

        # Set Rights
        newItem.rights = SFRRecordManager.setPipeDelimitedData(
            rights if isinstance(rights, list) else [rights],
            ['source', 'license', 'rights_reason', 'rights_statement', 'rights_date'],
            Rights,
            dParser=lambda x: dict(list(filter(lambda y: y[1] != '', x.items())))
        )

        # Set Contributors
        newItem.contributors = self.agentParser(item['contributors'], ['name', 'viaf', 'lcnaf', 'role'])

        return newItem

    @staticmethod
    def setPipeDelimitedData(data, fields, dType=None, dParser=None):
        return list(filter(None, [
            SFRRecordManager.parseDelimitedEntry(d, fields, dType, dParser)
            for d in list(filter(None, data))
        ]))

    @staticmethod
    def parseDelimitedEntry(dInst, fields, dType, dParser):
        dataEntry = dict(zip(fields, dInst.split('|')))
        if dParser is not None:
            dataEntry = dParser(dataEntry)
        if dType is None:
            return dataEntry

        return dType(**dataEntry)

    def getLanguage(self, langData):
        values = list(filter(lambda x: x != '', [v for _, v in langData.items()]))
        for v in values:
            for attr in ['alpha_2', 'alpha_3', 'name']:
                if attr == 'alpha_3': v = self.iso639_2b.get(v, v)

                pyLang = pycountry.languages.get(**{attr: v})

                if pyLang is not None:
                    return {
                        'language': pyLang.name,
                        'iso_2': getattr(pyLang, 'alpha_2', None),
                        'iso_3': getattr(pyLang, 'alpha_3', None)
                    }

    @staticmethod
    def parseLinkFlags(linkData):
        try:
            linkData['flags'] = json.loads(linkData['flags'])
        except json.decoder.JSONDecodeError:
            linkData['flags'] = {}

        return linkData

    def agentParser(self, agents, fields):
        outAgents = {}

        for agent in agents:
            agentParts = agent.split('|')

            while len(agentParts) < len(fields):
                agentParts.insert(1, '')

            rec = dict(zip(fields, agentParts))
            recKey = re.sub(r'[.,:\(\)]+', '', rec['name'].lower())

            if rec['name'] == '' and rec['viaf'] == '' and rec['lcnaf'] == '':
                continue
            
            existingMatch = False
            for oaKey, oa in outAgents.items():
                for checkField in ['viaf', 'lcnaf']:
                    if rec[checkField] and rec[checkField] != '' and rec[checkField] == oa[checkField]:
                        existingMatch = True
                        SFRRecordManager.mergeAgents(oa, rec)
                        break

                if existingMatch is False:
                    if jaro_winkler(oaKey, recKey) > 0.9:
                        SFRRecordManager.mergeAgents(oa, rec)
                        existingMatch = True
                        break

            if existingMatch is False:
                if 'role' in rec.keys():
                    rec['roles'] = list(set([rec['role']]))
                    del rec['role']
                outAgents[recKey] = rec


        return [a for _, a in outAgents.items()]

    def subjectParser(self, subjects):
        cleanSubjects = {}
        for subj in subjects:
            try:
                heading, auth, authNo = subj.split('|')
            except ValueError:
                authNoRev, authRev, *headRevArr = subj[::-1].split('|')
                authNo = authNoRev[::-1]
                auth = authRev[::-1]
                heading = ','.join(headRevArr)[::-1]

            if heading == '': continue

            cleanHeading = heading.strip(',.')
            headingKey = cleanHeading.lower()

            if headingKey in cleanSubjects.keys():
                if cleanSubjects[headingKey][1] == '' and auth != '':
                    cleanSubjects[headingKey][1] = auth
                    cleanSubjects[headingKey][2] = authNo
            else:
                cleanSubjects[headingKey] = [cleanHeading, auth, authNo] 

        cleanSubjStrs = ['|'.join(subj) for _, subj in cleanSubjects.items()]
        self.work.subjects = SFRRecordManager.setPipeDelimitedData(
            cleanSubjStrs, ['heading', 'authority', 'controlNo']
        )

    def normalizeDates(self, dates):
        outDates = set()
        for date in dates:
            try:
                dateValue, dateType = tuple(date.split('|'))
    
                cleanDate = re.search(r'\d+.*\d+', dateValue).group()

                outDates.add('{}|{}'.format(cleanDate, dateType))
            except (AttributeError, ValueError):
                pass

        return list(outDates)

    @staticmethod
    def mergeAgents(existing, new):
        if new['viaf'] != '':
            existing['viaf'] = new['viaf']

        if new['lcnaf'] != '':
            existing['lcnaf'] = new['lcnaf']

        if 'role' in new.keys():
            roleSet = set(existing['roles'])
            roleSet.add(new['role'])
            existing['roles'] = list(roleSet)

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
