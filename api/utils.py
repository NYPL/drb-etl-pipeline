from datetime import datetime
from flask import jsonify

class APIUtils():
    @staticmethod
    def normalizeQueryParams(params):
        paramDict = params.to_dict(flat=False)
        return {k: v for k, v in paramDict.items()}

    @staticmethod
    def extractParamPairs(paramPairs):
        return [
            tuple(p.split(':')) if len(p.split(':')) > 1 else (None, p)
            for p in paramPairs
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
        return {
            'prev_page_sort': list(hits[0].meta.sort),
            'next_page_sort': list(hits[-1].meta.sort)
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

            editionDict = dict(edition)
            editionDict['items'] = []

            for item in edition.items:
                itemDict = dict(item)
                itemDict['links'] = []
                for link in item.links:
                    itemDict['links'].append(dict(link))

                editionDict['items'].append(itemDict)

            if showAll is True or (showAll is False and len(editionDict['items']) > 0):
                workDict['editions'].append(editionDict)

        return workDict


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