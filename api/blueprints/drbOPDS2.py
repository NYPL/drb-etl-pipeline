from collections import defaultdict
from flask import Blueprint, current_app, request
from ..db import DBClient
from ..elastic import ElasticClient

from ..utils import APIUtils
from ..opds2 import Feed, Link, Metadata, Navigation, Publication, Facet, Group
from logger import createLog

logger = createLog(__name__)


opds = Blueprint('opds', __name__, url_prefix='/opds')


@opds.route('/', methods=['GET'])
def opdsRoot():
    logger.info('Returning Root OPDS2 feed')

    rootFeed = constructBaseFeed(request.path, 'Digital Research Books Home')

    return APIUtils.formatOPDS2Object(200, rootFeed)


@opds.route('/new', methods=['GET'])
def newPublications():
    logger.info('Returning OPDS2 feed of new publications')

    params = APIUtils.normalizeQueryParams(request.args)
    page = int(params.get('page', [1])[0]) - 1
    pageSize = int(params.get('size', [25])[0])

    dbClient = DBClient(current_app.config['DB_CLIENT'])

    baseFeed = constructBaseFeed(request.full_path, 'New Publications: Digital Research Books', grouped=True)

    pubCount, newPubs = dbClient.fetchNewWorks(page=page, size=pageSize)

    addPagingOptions(baseFeed, request.full_path, pubCount, page=page+1, pageSize=pageSize)

    addPublications(baseFeed, newPubs, grouped=True)

    return APIUtils.formatOPDS2Object(200, baseFeed)


@opds.route('/search', methods=['GET'])
def opdsSearch():
    logger.info('Returning OPDS2 feed of new publications')

    params = APIUtils.normalizeQueryParams(request.args)
    page = int(params.get('page', [1])[0]) - 1
    pageSize = int(params.get('size', [25])[0])

    queryList = []
    for queryField, queryTerms in params.items():
        esField = queryField if queryField != 'query' else 'keyword'
        queryList.extend([(esField, term) for term in queryTerms])

    esClient = ElasticClient(current_app.config['ES_CLIENT'])
    dbClient = DBClient(current_app.config['DB_CLIENT'])

    logger.info('Executing ES Query {}'.format(queryList))

    searchTerms = {'query': queryList, 'filter': [], 'sort': []}

    searchResult = esClient.searchQuery(searchTerms, page=page, perPage=pageSize)

    resultIds = [
        (r.uuid, [e.edition_id for e in r.meta.inner_hits.editions.hits])
        for r in searchResult.hits
    ]

    works = dbClient.fetchSearchedWorks(resultIds)

    searchFeed = constructBaseFeed(request.full_path, 'Search Results', grouped=True)

    addPagingOptions(searchFeed, request.full_path, searchResult.hits.total, page=page+1, pageSize=pageSize)

    addFacets(searchFeed, request.full_path, searchResult.aggregations.to_dict())

    addPublications(searchFeed, works, grouped=True)

    return APIUtils.formatOPDS2Object(200, searchFeed)


@opds.route('/publication/<uuid>', methods=['GET'])
def fetchPublication(uuid):
    logger.info('Returning OPDS2 publication for {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])

    workRecord = dbClient.fetchSingleWork(uuid)

    publication = createPublicationObject(workRecord, searchResult=False)

    publication.addLink({'rel': 'search', 'href': '/opds/search{?query,title,subject,author}', 'type': 'application/opds+json', 'templated': True})

    return APIUtils.formatOPDS2Object(200, publication)


def constructBaseFeed(path, title, grouped=False):
    feed = Feed()

    feedMetadata = Metadata(title=title)
    feed.addMetadata(feedMetadata)

    selfLink = Link(rel='self', href=path, type='application/opds+json')
    searchLink = Link(rel='search', href='/opds/search{?query,title,subject,author}', type='application/opds+json', templated=True)
    altLink = Link(rel='alternative', href='/', type='text/html')

    feed.addLinks([selfLink, searchLink, altLink])

    currentNavigation = Navigation(href=path, title=title, type='application/opds+json', rel='current')

    navOptions = [currentNavigation]

    if path != '/opds/':
        baseNavigation = Navigation(href='/opds', title='Home', type='application/opds+json', rel='home')
        navOptions.append(baseNavigation)

    if path != '/opds/new/':
        newNavigation = Navigation(href='/opds/new', title='New Works', type='application/opds+json', rel='http://opds-spec.org/sort/new')
        navOptions.append(newNavigation)

    if grouped is True:
        navGroup = Group(metadata={'title': 'Main Menu'})
        navGroup.addNavigations(navOptions)
        feed.addGroup(navGroup)
    else:
        feed.addNavigations(navOptions)

    return feed


def addPagingOptions(feed, path, publicationCount, page=1, pageSize=50):
    feed.metadata.addField('numberOfItems',  publicationCount)
    feed.metadata.addField('itemsPerPage', pageSize)
    feed.metadata.addField('currentPage', page)

    lastPage = int(publicationCount / pageSize)

    pagingRels = defaultdict(list)
    pagingRels[page].append('self')
    pagingRels[1].append('first')
    pagingRels[page - 1 if page > 1 else page].append('previous')
    pagingRels[page + 1 if page < lastPage else lastPage].append('next')
    pagingRels[lastPage].append('last')

    joinChar = '&' if '?' in path else '?'

    for pageNo, rels in pagingRels.items():
        relAttr = rels[0] if len(rels) == 0 else rels

        if 'self' in rels:
            selfLink = list(filter(lambda x: x.rel == 'self', feed.links))[0]
            selfLink.href = '{}?page={}'.format(selfLink.href, page)
            selfLink.rel = relAttr
        else:
            pageHref = '{}{}page={}'.format(path, joinChar, pageNo)
            feed.addLink({'rel': relAttr, 'href': pageHref, 'type': 'application/odps+json'})


def addPublications(feed, publications, grouped=False):
    opdsPubs = [createPublicationObject(pub) for pub in publications]

    if grouped is True:
        pubGroup = Group(metadata={'title': 'Publications'})
        pubGroup.addPublications(opdsPubs)
        feed.addGroup(pubGroup)
    else:
        feed.addPublications(opdsPubs)

def createPublicationObject(publication, searchResult=True):
        newPub = Publication()
        newPub.parseWorkToPublication(publication, searchResult=searchResult)

        return newPub


def addFacets(feed, path, facets):
    reducedFacets = APIUtils.formatAggregationResult(facets)

    opdsFacets = []

    for facet, options in reducedFacets.items():
        newFacet = Facet(metadata={'title': facet})
        facetOptions = [
            {
                'href': '{}&filter={}:{}'.format(path, facet, option['value']),
                'type': 'application/opds+json',
                'title': option['value'],
                'properties': {'numberOfItems': option['count']}
            }
            for option in options
        ]

        newFacet.addLinks(facetOptions)

        opdsFacets.append(newFacet)

    opdsFacets.append(Facet(
        metadata={'title': 'Show All Editions'},
        links=[
            {'href': '{}&showAll=true'.format(path), 'type': 'application/opds+json', 'title': 'True'},
            {'href': '{}&showAll=false'.format(path), 'type': 'application/opds+json', 'title': 'False'}
        ]
    ))

    feed.addFacets(opdsFacets)

    
