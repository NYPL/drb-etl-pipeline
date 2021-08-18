from flask import Flask
import jwt
import os
import pytest
from sqlalchemy.orm.exc import NoResultFound

from api.blueprints.drbCollection import (
    collectionCreate, collectionFetch, collectionDelete, collectionList,
    constructSortMethod, constructOPDSFeed, validateToken
)
from api.utils import APIUtils
from api.opdsUtils import OPDSUtils


class TestCollectionBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            formatOPDS2Object=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

    def test_collectionCreate_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.createCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        testRequestBody = {
            'title': 'Test Collection',
            'creator': 'Test Creator',
            'description': 'Test Description',
            'workUUIDs': ['uuid1', 'uuid2'],
            'editionIDs': ['ed1', 'ed2', 'ed3']
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.return_value = {'aud': 'testOwner'}

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testOPDS2Response'

            mockDBClient.assert_called_once_with('testDBClient')
            mockDB.createSession.assert_called_once()
            mockDB.createCollection.assert_called_once_with(
                'Test Collection', 'Test Creator', 'Test Description',
                'testOwner', workUUIDs=['uuid1', 'uuid2'],
                editionIDs=['ed1', 'ed2', 'ed3']
            )
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with('testUUID', mockDB)

            mockDecode.assert_called_once_with(
                'testToken', 'test', algorithms=['RS256'],
                options={'verify_aud': False}
            )

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                201, 'testOPDS2Feed'
            )

    def test_collectionCreate_error(self, testApp, mockUtils, mocker):
        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        testRequestBody = {
            'creator': 'Test Creator',
            'description': 'Test Description',
            'workUUIDs': ['uuid1', 'uuid2'],
            'editionIDs': ['ed1', 'ed2', 'ed3']
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.return_value = {'aud': 'testOwner'}

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testErrorResponse'

            mockUtils['formatResponseObject'].assert_called_once_with(
                400,
                'createCollection',
                {
                    'message':
                    'title, creator and description fields are required'
                    ', with one of workUUIDs or editionIDs to create a'
                    ' collection'

                }
            )

    def test_collectionFetch_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        with testApp.test_request_context('/?sort=title&page=3'):
            testAPIResponse = collectionFetch('testUUID')

            assert testAPIResponse == 'testOPDS2Response'

            mockDB.createSession.assert_called_once()

            mockFeedConstruct.assert_called_once_with(
                'testUUID', mockDB, sort='title', page=3, perPage=10
            )

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                200, 'testOPDS2Feed'
            )

    def test_collectionFetch_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.side_effect = NoResultFound

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        with testApp.test_request_context('/?sort=title&page=3'):
            testAPIResponse = collectionFetch('testUUID')

            assert testAPIResponse == 'testErrorResponse'

            mockDB.createSession.assert_called_once()

            mockFeedConstruct.assert_called_once_with(
                'testUUID', mockDB, sort='title', page=3, perPage=10
            )

            mockUtils['formatResponseObject'].assert_called_once_with(
                404, 'fetchCollection',
                {'message': 'Unable to locate collection testUUID'}
            )

    def test_collectionDelete_success(self, testApp, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.deleteCollection.return_value = 1

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.return_value = {'aud': 'testOwner'}

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionDelete('testUUID')

            assert testAPIResponse[0].status_code == 200
            assert testAPIResponse[0].json == {'message': 'Deleted testUUID'}

            mockDB.createSession.assert_called_once()
            mockDB.deleteCollection.assert_called_once_with(
                'testUUID', 'testOwner'
            )
            mockDB.session.commit.assert_called_once()

    def test_collectionDelete_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.deleteCollection.return_value = 0

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.return_value = {'aud': 'testOwner'}

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionDelete('testUUID')

            assert testAPIResponse == 'testErrorResponse'

            mockDB.createSession.assert_called_once()
            mockDB.deleteCollection.assert_called_once_with(
                'testUUID', 'testOwner'
            )

            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'deleteCollection',
                {'message': 'No collection with UUID testUUID exists'}
            )

    def test_collectionList_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchCollections.return_value = [
            mocker.MagicMock(uuid='uuid1'), mocker.MagicMock(uuid='uuid2')
        ]

        mockFeed = mocker.MagicMock()
        mockFeedInit = mocker.patch('api.blueprints.drbCollection.Feed')
        mockFeedInit.return_value = mockFeed

        mockPaging = mocker.patch.object(OPDSUtils, 'addPagingOptions')

        mockConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockConstruct.side_effect = ['group1', 'group2']

        mockUtils['formatOPDS2Object'].return_value = 'testOPDSResponse'

        with testApp.test_request_context('/list'):
            testResponse = collectionList()

            assert testResponse == 'testOPDSResponse'

            mockDB.createSession.assert_called_once()
            mockDB.fetchCollections.assert_called_once_with(
                sort='title', page=1, perPage=10
            )

            mockFeedInit.assert_called_once()
            mockFeed.addMetadata.assert_called_once_with(
                {'title': 'Digital Research Books Collections'}
            )
            mockFeed.addLink.assert_called_once_with({
                'rel': 'self',
                'href': '/list',
                'type': 'application/opds+json'
            })

            mockPaging.assert_called_once_with(
                mockFeed, '/list?', 2, page=1, perPage=10
            )

            mockConstruct.assert_has_calls([
                mocker.call(
                    'uuid1', mockDB, perPage=5, path='/collection/uuid1'
                ),
                mocker.call(
                    'uuid2', mockDB, perPage=5, path='/collection/uuid2'
                )
            ])

            mockFeed.addGroup.assert_has_calls([
                mocker.call('group1'), mocker.call('group2')
            ])

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                200, mockFeed
            )

    def test_collectionList_sort_error(self, testApp, mockUtils):
        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        with testApp.test_request_context('/list?sort=error'):
            testResponse = collectionList()

            assert testResponse == 'testErrorResponse'

            mockUtils['formatResponseObject'].assert_called_once_with(
                400, 'collectionList',
                {'message': 'valid sort fields are title and creator'}
            )

    def test_constructSortMethod_string(self, mocker):
        sortMethod, reversed = constructSortMethod('test')

        testSorts = [
            mocker.MagicMock(metadata=mocker.MagicMock(id=1, test='b')),
            mocker.MagicMock(metadata=mocker.MagicMock(id=2, test='A')),
            mocker.MagicMock(metadata=mocker.MagicMock(id=3, test='c')),
        ]

        sortedList = sorted(testSorts, key=sortMethod, reverse=reversed)

        assert [x.metadata.id for x in sortedList] == [2, 1, 3]

    def test_constructSortMethod_int_reversed(self, mocker):
        sortMethod, reversed = constructSortMethod('test:desc')

        testSorts = [
            mocker.MagicMock(metadata=mocker.MagicMock(id=1, test=3)),
            mocker.MagicMock(metadata=mocker.MagicMock(id=2, test=1)),
            mocker.MagicMock(metadata=mocker.MagicMock(id=3, test=2)),
        ]

        sortedList = sorted(testSorts, key=sortMethod, reverse=reversed)

        assert [x.metadata.id for x in sortedList] == [1, 3, 2]

    def test_constructOPDSFeed_success(self, testApp, mockUtils, mocker):
        mockFeed = mocker.MagicMock()
        mockFeedInit = mocker.patch('api.blueprints.drbCollection.Feed')
        mockFeedInit.return_value = mockFeed

        mockPub = mocker.MagicMock()
        mockPubInit = mocker.patch('api.blueprints.drbCollection.Publication')
        mockPubInit.return_value = mockPub

        mockDB = mocker.MagicMock()
        mockDB.fetchSingleCollection.return_value = mocker.MagicMock(
            title='Test Collection',
            creator='Test Creator',
            description='Test Description',
            editions=[
                mocker.MagicMock(id=1), mocker.MagicMock(id=2)
            ]
        )

        mocker.patch.dict(os.environ, {'ENVIRONMENT': 'test'})

        mockPaging = mocker.patch.object(OPDSUtils, 'addPagingOptions')

        mockSortCon = mocker.patch(
            'api.blueprints.drbCollection.constructSortMethod'
        )
        mockSortCon.return_value = (lambda x: str(x), False)

        with testApp.test_request_context('/collections/test'):
            testOPDSFeed = constructOPDSFeed('testUUID', mockDB, sort='test')

            assert testOPDSFeed == mockFeed

            mockFeed.addMetadata.assert_called_once_with({
                'title': 'Test Collection',
                'creator': 'Test Creator',
                'description': 'Test Description'
            })
            mockFeed.addLink.assert_called_once_with({
                'rel': 'self',
                'href': '/collections/test',
                'type': 'application/opds+json'
            })
            mockFeed.addPublications.assert_called_once()

            assert mockPub.parseEditionToPublication.call_count == 2
            mockPub.addLink.assert_has_calls([
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/1',
                    'type': 'text/html'
                }),
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/2',
                    'type': 'text/html'
                })
            ])

            mockSortCon.assert_called_once_with('test')

            mockPaging.assert_called_once_with(
                mockFeed, '/collections/test?', 2, page=1, perPage=10
            )

    def test_validateToken_success(self, testApp, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.return_value = {'aud': 'testOwner'}

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            decoratedFunction()

            mockDecode.assert_called_once_with(
                'testToken', 'test', algorithms=['RS256'],
                options={'verify_aud': False}
            )

            mockFunc.assert_called_once_with(user='testOwner')

    def test_validateToken_error_no_header(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context('/'):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                403, 'authenticationError',
                {'message': 'Authorization Bearer token required'}
            )

    def test_validateToken_error_jwt(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockDecode = mocker.patch.object(jwt, 'decode')
        mockDecode.side_effect = jwt.DecodeError

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                403, 'authenticationError',
                {'message': 'Unable to decode auth token'}
            )
