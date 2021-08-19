from collections import OrderedDict
from datetime import datetime
from hashlib import scrypt
from flask import jsonify
from math import ceil
import re

class APIUtils():
    QUERY_TERMS = [
        'keyword', 'title', 'author', 'subject', 'viaf', 'lcnaf',
        'date', 'startYear', 'endYear', 'language', 'format', 'showAll'
    ]

    FORMAT_CROSSWALK = {
        'epub_zip': ['application/epub+zip', 'application/epub+xml'],
        'epub_xml': ['application/epub+zip', 'application/epub+xml'],
        'html': ['text/html'],
        'html_edd': ['application/html+edd'],
        'pdf': ['application/pdf'],
        'webpub_json': ['application/webpub+json']
    }

    @staticmethod
    def normalizeQueryParams(params):
        paramDict = params.to_dict(flat=False)
        return {k: v for k, v in paramDict.items()}

    @classmethod
    def extractParamPairs(cls, param, pairs):
        outPairs = []

        for pairStr in pairs.get(param, []):
            if len(re.findall(r'"', pairStr)) % 2 != 0:
                pairStr = ''.join(pairStr.rsplit('"', 1))

            # Regex to split query string on field terms
            queryTermRegex = ',*({}):'.format('|'.join(cls.QUERY_TERMS))\
                .encode('unicode-escape').decode()

            pairs = list(filter(lambda x: x != '', re.split(queryTermRegex, pairStr)))

            i = 0 
            while True:
                pairElements = pairs[i:i+2]

                if len(pairElements) == 1 or pairElements[0] not in cls.QUERY_TERMS:
                    pairSet = (param, pairs[i])
                    i += 1
                else:
                    pairSet = (pairElements[0], ':'.join(pairElements[1:]))
                    i += 2

                outPairs.append(pairSet)

                if i >= len(pairs): break

        return outPairs

    @classmethod
    def formatAggregationResult(cls, aggregations, parentKey=None):
        aggs = {}

        for key, value in aggregations.items():
            if key == 'buckets':
                aggs[parentKey] = [
                    {'value': b['key'], 'count': b['editions_per']['doc_count']}
                    for b in value
                ]
                return aggs
            
            if isinstance(value, dict):
                aggs = {**aggs, **cls.formatAggregationResult(value, parentKey=key)}

        return aggs

    @staticmethod
    def formatPagingOptions(page, pageSize, totalHits):
        if totalHits == 0: return {}

        lastPage = ceil(totalHits / pageSize)

        return {
            'recordsPerPage': pageSize,
            'firstPage': 1,
            'previousPage': page - 1 if page > 1 else None,
            'currentPage': page,
            'nextPage': page + 1 if page < lastPage else None,
            'lastPage': lastPage
        }

    @classmethod
    def formatWorkOutput(cls, works, identifiers, showAll=True, formats=None):
        if isinstance(works, list):
            outWorks = []
            workDict = {str(work.uuid): work for work in works}

            for workUUID, editionIds in identifiers:
                work = workDict.get(workUUID, None)

                if work is None: continue

                outWorks.append(cls.formatWork(work, editionIds, showAll, formats=formats))
            
            return outWorks
        else:
            formattedWork =  cls.formatWork(works, None, showAll)
            formattedWork['editions'].sort(key=lambda x: x['publication_date'] if x['publication_date'] else 9999)

            return formattedWork

    @classmethod
    def formatWork(cls, work, editionIds, showAll, formats=None):
        workDict = dict(work)
        workDict['edition_count'] = len(work.editions)

        orderedEds = OrderedDict.fromkeys(editionIds) if editionIds else OrderedDict()

        for edition in work.editions:
            if editionIds and edition.id not in editionIds:
                continue
            
            editionDict = cls.formatEdition(edition, formats=formats)

            if showAll is True or (showAll is False and len(editionDict['items']) > 0):
                orderedEds[edition.id] = editionDict

        workDict['editions'] = list(filter(None, [e for _, e in orderedEds.items()]))

        return workDict

    @classmethod
    def formatEditionOutput(cls, edition, records=None, showAll=False):
        return cls.formatEdition(edition, records, showAll=showAll)

    @classmethod
    def formatEdition(cls, edition, records=None, formats=None, showAll=False):
        editionDict = dict(edition)
        editionDict['edition_id'] = edition.id
        editionDict['work_uuid'] = edition.work.uuid
        editionDict['publication_date'] = edition.publication_date.year if edition.publication_date else None
        editionDict['links'] = [
            {'link_id': l.id, 'mediaType': l.media_type, 'url': l.url}
            for l in edition.links
        ]

        editionDict['items'] = []
        for item in edition.items:
            itemDict = dict(item)
            itemDict['item_id'] = item.id
            itemDict['location'] = item.physical_location['name'] if item.physical_location else None

            itemDict['links'] = list(filter(None, [
                {'link_id': l.id, 'mediaType': l.media_type, 'url': l.url}
                if not formats or l.media_type in formats else None
                for l in item.links
            ]))

            # TEMPORARY: Remove application/webpub+json files
            # while new reader is under development. Remove any items that have
            # no links as a result
            itemDict['links'] = list(filter(lambda x: x['mediaType'] != 'application/webpub+json', itemDict['links']))
            if len(itemDict['links']) < 1: continue

            itemDict['rights'] = [
                {'source': r.source, 'license': r.license, 'rightsStatement': r.rights_statement}
                for r in item.rights
            ]

            if len(itemDict['links']) < 1: continue

            editionDict['items'].append(itemDict)

        if records is not None:
            itemsByLink = {}
            for item in editionDict['items']:
                for link in item['links']:
                    itemsByLink[link['url']] = item
            
            editionDict['instances'] = []
            for rec in records:
                formattedRec = cls.formatRecord(rec, itemsByLink)

                if showAll is False and len(formattedRec['items']) < 1:
                    continue

                editionDict['instances'].append(formattedRec)

            del editionDict['items']

        return editionDict

    @classmethod
    def formatRecord(cls, record, itemsByLink):
        outRecord = {
            'instance_id': record.id,
            'title': record.title,
            'publication_place': record.spatial,
            'extent': record.extent,
            'summary': record.abstract,
            'table_of_contents': record.table_of_contents
        }
        
        outRecord['authors'] = cls.formatPipeDelimitedData(record.authors, ['name', 'viaf', 'lcnaf', 'primary'])
        outRecord['contributors'] = cls.formatPipeDelimitedData(record.contributors, ['name', 'viaf', 'lcnaf', 'rolse'])
        outRecord['publishers'] = cls.formatPipeDelimitedData(record.publisher, ['name', 'viaf', 'lcnaf'])
        outRecord['dates'] = cls.formatPipeDelimitedData(record.dates, ['date', 'type'])
        outRecord['languages'] = cls.formatPipeDelimitedData(record.languages, ['language', 'iso_2', 'iso_3'])
        outRecord['identifiers'] = cls.formatPipeDelimitedData(record.identifiers, ['identifier', 'authority'])

        recordItems = {}
        for hasPart in record.has_part:
            _, url, *_ = hasPart.split('|')
            urlItem = itemsByLink.get(re.sub(r'https?:\/\/', '', url), None)
            
            if urlItem:
                recordItems[urlItem['item_id']] = urlItem
        
        outRecord['items'] = [item for _, item in recordItems.items()]

        return outRecord

    @classmethod
    def formatLinkOutput(cls, link):
        linkItem = dict(link.items[0])
        linkItem['item_id'] = link.items[0].id

        linkEdition = dict(link.items[0].edition)
        linkEdition['edition_id'] = link.items[0].edition.id
        linkEdition['work_uuid'] = link.items[0].edition.work.uuid
        linkEdition['publication_date'] = link.items[0].edition.publication_date.year if link.items[0].edition.publication_date else None

        linkDict = dict(link)
        linkDict['link_id'] = link.id
        linkDict['work'] = dict(link.items[0].edition.work)
        linkDict['work']['editions'] = [linkEdition]
        linkDict['work']['editions'][0]['items'] = [linkItem]

        return linkDict

    @classmethod
    def formatLanguages(cls, aggregations, counts=False):
        if counts:
            return sorted([
                {'language': lang.key, 'work_total': lang.work_totals.doc_count}
                for lang in aggregations.languages.languages.buckets
            ], key=lambda x: x['work_total'], reverse=True)
        else:
            return sorted(
                [{'language': lang.key} for lang in aggregations.languages.languages.buckets],
                key=lambda x: x['language']
            )

    @classmethod
    def formatTotals(cls, response):
        return {r[0]: r[1] for r in response}

    @classmethod
    def flatten(cls, nested):
        try:
            iter(nested)
        except TypeError:
            yield nested
        else:
            for elem in nested:
                yield from cls.flatten(elem)
    
    @staticmethod
    def formatResponseObject(status, responseType, datablock):
        return (
            jsonify({
                'status': status,
                'timestamp': datetime.utcnow(),
                'responseType': responseType,
                'data': datablock
            }),
            status
        )

    @staticmethod
    def formatOPDS2Object(status, feedObject):
        return (jsonify(dict(feedObject)), status)

    @staticmethod
    def formatPipeDelimitedData(data, fields):
        if data is None:
            return None
        elif isinstance(data, list):
            dataList = list(filter(None, data))
            return [dict(zip(fields, d.split('|'))) for d in dataList]
        else:
            return dict(zip(fields, data.split('|')))

    @staticmethod
    def validatePassword(password, hash, salt):
        password = password.encode('utf-8')

        hashedPassword = scrypt(password, salt=salt, n=2**14, r=8, p=1)

        return hashedPassword == hash
