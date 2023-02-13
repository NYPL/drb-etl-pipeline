from base64 import b64decode
from flask import Blueprint, request, current_app, jsonify
from functools import wraps
import os
import re
from sqlalchemy.orm.exc import NoResultFound

from ..db import DBClient
from ..opdsUtils import OPDSUtils
from ..utils import APIUtils
from ..opds2 import Feed, Publication
from logger import createLog
from model import Work
from model.postgres.collection import COLLECTION_EDITIONS
from datetime import date

logger = createLog(__name__)

collection = Blueprint('collection', __name__, url_prefix='/collection')


def validateToken(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        logger.debug(request.headers)

        headers = {k.lower(): v for k, v in request.headers.items()}

        try:
            _, loginPair = headers['authorization'].split(' ')
            loginBytes = loginPair.encode('utf-8')
            user, password = b64decode(loginBytes).decode('utf-8').split(':')
        except KeyError:
            return APIUtils.formatResponseObject(
                403, 'authResponse', {'message': 'user/password not provided'}
            )

        dbClient = DBClient(current_app.config['DB_CLIENT'])
        dbClient.createSession()

        user = dbClient.fetchUser(user)

        if not user or APIUtils.validatePassword(password, user.password, user.salt) is False:
            return APIUtils.formatResponseObject(
                401, 'authResponse', {'message': 'invalid user/password'}
            )

        dbClient.closeSession()

        kwargs['user'] = user.user

        return func(*args, **kwargs)

    return decorator


@collection.route('', methods=['POST'])
@validateToken
def collectionCreate(user=None):
    logger.info('Creating new collection')

    collectionData = request.json
    dataKeys = collectionData.keys()

    if len(set(dataKeys) & set(['title', 'creator', 'description'])) < 3\
            or len(set(dataKeys) & set(['workUUIDs', 'editionIDs'])) == 0:
        errMsg = {
            'message':
                'title, creator and description fields are required'
                ', with one of workUUIDs or editionIDs to create a collection'
        }

        return APIUtils.formatResponseObject(400, 'createCollection', errMsg)

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    newCollection = dbClient.createCollection(
        collectionData['title'],
        collectionData['creator'],
        collectionData['description'],
        user,
        workUUIDs=collectionData.get('workUUIDs', []),
        editionIDs=collectionData.get('editionIDs', [])
    )

    dbClient.session.commit()

    logger.info('Created collection {}'.format(newCollection))

    opdsFeed = constructOPDSFeed(newCollection.uuid, dbClient)

    return APIUtils.formatOPDS2Object(201, opdsFeed)

@collection.route('/update/<uuid>', methods=['POST'])
@validateToken
def collectionUpdate(uuid, user=None):
    logger.info('Handling collection update request')

    collectionData = request.json
    dataKeys = collectionData.keys()

    if {'title', 'creator', 'description'}.issubset(set(dataKeys)) == False\
            or len(set(dataKeys) & set(['workUUIDs', 'editionIDs'])) == 0:
        errMsg = {
            'message':
                'title, creator and description fields are required'
                ', with one of workUUIDs or editionIDs to create a collection'
        }

        return APIUtils.formatResponseObject(400, 'createCollection', errMsg)

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    #Getting the collection the user wants to replace
    try:
        collection = dbClient.fetchSingleCollection(uuid)
    except NoResultFound:
        errMsg = {'message': 'Unable to locate collection {}'.format(uuid)}
        return APIUtils.formatResponseObject(404, 'fetchSingleCollection', errMsg)

    workUUIDs=collectionData.get('workUUIDs', [])
    editionIDs=collectionData.get('editionIDs', [])

    collection.title = collectionData['title']
    collection.creator = collectionData['creator']
    collection.description = collectionData['description']

    #Deleting the rows of collection_editions that were in the original collection
    dbClient.session.execute(COLLECTION_EDITIONS.delete().where(COLLECTION_EDITIONS.c.collection_id == collection.id))

    #Inserting rows of collection_editions based on workUUIDs/editionIDs arrays
    if len(editionIDs) > 0:
        for editID in editionIDs:
            dbClient.session.execute(COLLECTION_EDITIONS.insert().values \
                (collection_id = collection.id, edition_id = editID))

    if len(workUUIDs) > 0:
        collectionWorks = dbClient.session.query(Work)\
            .join(Work.editions)\
            .filter(Work.uuid.in_(workUUIDs))\
            .all()

        for work in collectionWorks:
            editions = list(sorted(
                    [ed for ed in work.editions],
                    key=lambda x: x.publication_date
                    if x.publication_date else date.today()
            ))
        
            for edition in editions:
                dbClient.session.execute(COLLECTION_EDITIONS.insert().values \
                    (collection_id = collection.id, edition_id = edition.id))

    dbClient.session.commit()

    logger.info('Replaced collection {}'.format(collection))

    opdsFeed = constructOPDSFeed(collection.uuid, dbClient)

    return APIUtils.formatOPDS2Object(201, opdsFeed)

@collection.route('/<uuid>', methods=['GET'])
def collectionFetch(uuid):
    logger.info('Fetching collection identified by {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    sort = request.args.get('sort', None)
    page = int(request.args.get('page', 1))
    perPage = int(request.args.get('perPage', 10))

    try:
        opdsFeed = constructOPDSFeed(
            uuid, dbClient, sort=sort, page=page, perPage=perPage
        )
    except NoResultFound:
        errMsg = {'message': 'Unable to locate collection {}'.format(uuid)}
        return APIUtils.formatResponseObject(404, 'fetchCollection', errMsg)

    return APIUtils.formatOPDS2Object(200, opdsFeed)


@collection.route('/<uuid>', methods=['DELETE'])
@validateToken
def collectionDelete(uuid, user=None):
    logger.info('Deleting collection {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    deleteCount = dbClient.deleteCollection(uuid, user)

    if deleteCount is None or deleteCount < 1:
        errMsg = {'message': 'No collection with UUID {} exists'.format(uuid)}
        return APIUtils.formatResponseObject(404, 'deleteCollection', errMsg)

    dbClient.session.commit()

    logger.info('Successfully Deleted Collection')

    return (jsonify({'message': 'Deleted {}'.format(uuid)}), 200)


@collection.route('/list', methods=['GET'])
def collectionList():
    logger.info('Listing all collections')

    sort = request.args.get('sort', 'title')
    page = int(request.args.get('page', 1))
    perPage = int(request.args.get('perPage', 10))

    if not re.match(r'(?:title|creator)(?::(?:asc|desc))*', sort):
        return APIUtils.formatResponseObject(
            400, 'collectionList',
            {'message': 'valid sort fields are title and creator'}
        )

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    collections = dbClient.fetchCollections(
        sort=sort, page=page, perPage=perPage
    )

    opdsFeed = Feed()

    opdsFeed.addMetadata({
        'title': 'Digital Research Books Collections'
    })

    opdsFeed.addLink({
        'rel': 'self',
        'href': request.path,
        'type': 'application/opds+json'
    })

    OPDSUtils.addPagingOptions(
        opdsFeed, request.full_path, len(collections),
        page=page, perPage=perPage
    )

    for collection in collections:
        uuid = collection.uuid

        path = '/collection/{}'.format(uuid)

        group = constructOPDSFeed(uuid, dbClient, perPage=5, path=path)

        opdsFeed.addGroup(group)

    return APIUtils.formatOPDS2Object(200, opdsFeed)


def constructSortMethod(sort):
    sortSettings = sort.split(':')

    def sortEds(ed):
        sortValue = getattr(ed.metadata, sortSettings[0])

        if isinstance(sortValue, str):
            sortValue = sortValue.lower()

        return sortValue

    if len(sortSettings) == 2:
        reversed = True if sortSettings[1].lower() == 'desc' else False
    else:
        reversed = False

    return (sortEds, reversed)


def constructOPDSFeed(
    uuid, dbClient, sort=None, page=1, perPage=10, path=None
):
    collection = dbClient.fetchSingleCollection(uuid)

    opdsFeed = Feed()

    opdsFeed.addMetadata({
        'title': collection.title,
        'creator': collection.creator,
        'description': collection.description
    })

    path = request.full_path\
        if str(uuid) in request.path\
        else '/collection/{}'.format(uuid)

    opdsFeed.addLink({
        'rel': 'self', 'href': path, 'type': 'application/opds+json'
    })

    host = 'digital-research-books-beta'\
        if os.environ['ENVIRONMENT'] == 'production' else 'drb-qa'

    opdsPubs = []
    for ed in collection.editions:
        pub = Publication()

        pub.parseEditionToPublication(ed)
        pub.addLink({
            'rel': 'alternate',
            'href': 'https://{}.nypl.org/edition/{}'.format(host, ed.id),
            'type': 'text/html'
        })

        opdsPubs.append(pub)

    if sort:
        sorter, reversed = constructSortMethod(sort)
        opdsPubs.sort(key=sorter, reverse=reversed)

    start = (page - 1) * perPage
    end = start + perPage
    opdsFeed.addPublications(opdsPubs[start:end])

    OPDSUtils.addPagingOptions(
        opdsFeed, path, len(opdsPubs), page=page, perPage=perPage
    )

    return opdsFeed
