from datetime import datetime
from flask import jsonify
from math import ceil
import re

class APIUtils():
    @staticmethod
    def normalizeQueryParams(params):
        paramDict = params.to_dict(flat=False)
        return {k: v for k, v in paramDict.items()}

    @staticmethod
    def extractParamPairs(param, pairs):
        outPairs = []

        for pairStr in pairs.get(param, []):
            for pair in pairStr.split(','):
                pairSet = tuple(pair.split(':')) if len(pair.split(':')) > 1 else (param, pair)
                outPairs.append(pairSet)

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
    def formatWorkOutput(cls, works, identifiers, showAll=True):
        if isinstance(works, list):
            outWorks = []
            workDict = {str(work.uuid): work for work in works}

            for workUUID, editionIds in identifiers:
                work = workDict.get(workUUID, None)

                if work is None: continue

                outWorks.append(cls.formatWork(work, editionIds, showAll))
            
            return outWorks
        else:
            return cls.formatWork(works, None, showAll)

    @classmethod
    def formatWork(cls, work, editionIds, showAll):
        workDict = dict(work)
        workDict['edition_count'] = len(work.editions)
        workDict['editions'] = []

        for edition in work.editions:
            if editionIds and edition.id not in editionIds:
                continue
            
            editionDict = cls.formatEdition(edition)

            if showAll is True or (showAll is False and len(editionDict['items']) > 0):
                workDict['editions'].append(editionDict)

        return workDict

    @classmethod
    def formatEditionOutput(cls, edition, records=None, showAll=False):
        return cls.formatEdition(edition, records)

    @classmethod
    def formatEdition(cls, edition, records=None):
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

            itemDict['links'] = [
                {'link_id': l.id, 'mediaType': l.media_type, 'url': l.url}
                for l in item.links
            ]

            itemDict['rights'] = [
                {'source': r.source, 'license': r.license, 'rightsStatement': r.rights_statement}
                for r in item.rights
            ]

            editionDict['items'].append(itemDict)

        if records is not None:
            itemsByLink = {}
            for item in editionDict['items']:
                for link in item['links']:
                    itemsByLink[link['url']] = item
            editionDict['instances'] = [cls.formatRecord(rec, itemsByLink) for rec in records]

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
