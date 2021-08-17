import boto3
from flask import Blueprint, request, current_app, jsonify
from functools import wraps
import jwt
import os

from ..db import DBClient
from ..opdsUtils import OPDSUtils
from ..utils import APIUtils
from ..opds2 import Feed, Publication
from logger import createLog

logger = createLog(__name__)

collection = Blueprint('collection', __name__, url_prefix='/collection')


def validateToken(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        logger.debug(request.headers)

        errMsg = None

        publicKey = os.environ['NYPL_API_CLIENT_PUBLIC_KEY']

        headers = {k.lower(): v for k, v in request.headers.items()}

        try:
            _, authToken = headers['authorization'].split(' ')

            decoded = jwt.decode(
                authToken,
                publicKey,
                algorithms=['RS256'],
                options={'verify_aud': False}
            )

            logger.debug('Decoded token for user {}'.format(decoded['aud']))

            kwargs['user'] = decoded['aud']
        except KeyError:
            errMsg = 'Authorization Bearer token required'
        except jwt.DecodeError:
            errMsg = 'Unable to decode auth token'
        except jwt.InvalidTokenError:
            errMsg = 'Invalid auth token provided'
        except jwt.ExpiredSignatureError:
            errMsg = 'Supplied auth token has expired'

        if errMsg:
            return APIUtils.formatResponseObject(
                403, 'authenticationError', {'message': errMsg}
            )

        logger.debug('Successfully validated authentication token')

        return func(*args, **kwargs)

    return decorator


@collection.route('/', methods=['POST'])
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

    return constructOPDSFeed(newCollection.uuid, dbClient)


@collection.route('/<uuid>', methods=['GET'])
def collectionFetch(uuid):
    logger.info('Fetching collection identified by {}'.format(uuid))

    dbClient = DBClient(current_app.config['DB_CLIENT'])
    dbClient.createSession()

    sort = request.args.get('sort', None)
    page = int(request.args.get('page', 1))
    perPage = int(request.args.get('perPage', 10))

    return constructOPDSFeed(
        uuid, dbClient, sort=sort, page=page, perPage=perPage
    )


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


def constructOPDSFeed(uuid, dbClient, sort=None, page=1, perPage=10):
    collection = dbClient.fetchSingleCollection(uuid)

    if not collection:
        errMsg = {'message': 'Unable to locate collection {}'.format(uuid)}
        return APIUtils.formatResponseObject(404, 'fetchCollection', errMsg)

    opdsFeed = Feed()

    opdsFeed.addMetadata({
        'title': collection.title,
        'creator': collection.creator,
        'description': collection.description
    })

    opdsFeed.addLink({
        'rel': 'self',
        'href': request.path,
        'type': 'application/opds+json'
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
        opdsFeed, request.full_path, len(opdsPubs), page=page, perPage=perPage
    )

    return APIUtils.formatOPDS2Object(200, opdsFeed)
