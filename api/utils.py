from datetime import datetime
from flask import jsonify

class APIUtils():
    @staticmethod
    def normalizeQueryParams(params):
        paramDict = params.to_dict(flat=False)
        return {k: v for k, v in paramDict.items()}

    @staticmethod
    def extractParamPairs(param, pairs):
        return [
            tuple(p.split(':')) if len(p.split(':')) > 1 else (param, p)
            for p in pairs.get(param, [])
        ]

    @classmethod
    def formatAggregationResult(cls, aggregations):
        for key, value in aggregations.items():
            if key == 'buckets':
                return [
                    {'value': b['key'], 'count': b['editions_per_language']['doc_count']}
                    for b in value
                ]
            elif isinstance(value, dict):
                return cls.formatAggregationResult(value)

    @staticmethod
    def formatPagingOptions(hits):
        if len(hits) == 0: return {}

        return {
            'prevPageSort': list(hits[0].meta.sort),
            'nextPageSort': list(hits[-1].meta.sort)
        }

    @classmethod
    def formatWorkOutput(cls, works, identifiers=None, showAll=True):
        if isinstance(works, list):
            outWorks = []
            editionIds = []

            if identifiers:
                editionIds = list(cls.flatten([i[1] for i in identifiers]))

            for work in works:
                outWorks.append(cls.formatWork(work, editionIds, showAll))
            
            return outWorks
        else:
            return cls.formatWork(works, None, showAll)

    @classmethod
    def formatWork(cls, work, editionIds, showAll):
        workDict = dict(work)
        workDict['editions'] = []

        for edition in work.editions:
            if editionIds and edition.id not in editionIds:
                continue

            editionDict = cls.formatEdition(edition)

            if showAll is True or (showAll is False and len(editionDict['items']) > 0):
                workDict['editions'].append(editionDict)

        return workDict

    @classmethod
    def formatEditionOutput(cls, edition, showAll):
        return cls.formatEdition(edition)

    @classmethod
    def formatEdition(cls, edition):
        editionDict = dict(edition)
        editionDict['edition_id'] = edition.id
        editionDict['items'] = []

        for item in edition.items:
            itemDict = dict(item)
            itemDict['item_id'] = item.id
            itemDict['links'] = []
            for link in item.links:
                itemDict['links'].append({'link_id': link.id, 'mediaType': link.media_type})

            editionDict['items'].append(itemDict)

        return editionDict

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