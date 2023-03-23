from flask import Flask
import os
import pytest
from sqlalchemy.orm.exc import NoResultFound

from api.blueprints.drbCollection import (
    collectionCreate, collectionFetch, collectionReplace, collectionUpdate, collectionDelete, 
    collectionDeleteWorkEdition, collectionList, constructSortMethod, constructOPDSFeed, validateToken
)
from api.utils import APIUtils
from api.opdsUtils import OPDSUtils


class TestCollectionBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            formatOPDS2Object=mocker.DEFAULT,
            validatePassword=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

    def test_collectionReplace_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        testUpdatedCollection = {
            'title': 'Updated Test Collection',
            'creator': 'Updated Test Creator',
            'description': 'Updated Test Description',
            'editionIDs': ['ed11', 'ed22']
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        with testApp.test_request_context(
            '/replace/testUUID',
            json=testUpdatedCollection,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionReplace('testUUID')

            assert testAPIResponse == 'testOPDS2Response'

            assert mockDBClient.call_count == 2
            assert mockDB.createSession.call_count == 2
            assert mockDB.session.execute.call_count == 1
            mockDB.fetchSingleCollection.assert_called_once_with('testUUID')
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with(
                'testUUID', mockDB
            )

            mockBase64.assert_called_once_with(b'testAuth')

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                201, 'testOPDS2Feed'
            )

    def test_collectionReplace_fail(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        testFailCollection = {
            'title': 'Updated Test Collection',
            'creator': 'Updated Test Creator'
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/replace/testUUID',
            json=testFailCollection,
            headers={'Authorization': 'Basic testAuth'}
        ):

            testAPIResponse = collectionReplace('testUUID')

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


    def test_collectionUpdate_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        with testApp.test_request_context(
            '/update/testUUID?title=newTitle',
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionUpdate('testUUID')

            assert testAPIResponse == 'testOPDS2Response'

            assert mockDBClient.call_count == 2
            assert mockDB.createSession.call_count == 2
            mockDB.fetchSingleCollection.assert_called_once_with('testUUID')
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with(
                'testUUID', mockDB
            )

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                200, 'testOPDS2Feed'
            )

    def test_collectionUpdate_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')
        
        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        with testApp.test_request_context(
            '/update/testUUID',
            headers={'Authorization': 'Basic testAuth'}
        ):

            testAPIResponse = collectionUpdate('testUUID')

            assert testAPIResponse == 'testErrorResponse'

            mockUtils['formatResponseObject'].assert_called_once_with(
                400,
                'updateCollection',
                {
                    'message':
                    'At least one of these fields(title, creator, description, etc.) are required'
                }
            )

    def test_staticCollectionCreate_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        newCollection = mocker.MagicMock(uuid='testUUID')
        mockDB.createStaticCollection.return_value = newCollection

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection._constructOPDSFeedForCollection'
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

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testOPDS2Response'

            assert mockDBClient.call_count == 2
            assert mockDB.createSession.call_count == 2
            mockDB.createStaticCollection.assert_called_once_with(
                'Test Collection', 'Test Creator', 'Test Description',
                'testUser', workUUIDs=['uuid1', 'uuid2'],
                editionIDs=['ed1', 'ed2', 'ed3']
            )
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with(newCollection, mockDB)

            mockBase64.assert_called_once_with(b'testAuth')

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                201, 'testOPDS2Feed'
            )

    def test_automaticCollectionCreate_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        newCollection = mocker.MagicMock(
            uuid='testUUID', type="automatic"
        )
        mockDB.createAutomaticCollection.return_value = newCollection

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection._constructOPDSFeedForCollection'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        testRequestBody = {
            'title': 'Test Collection',
            'creator': 'Test Creator',
            'description': 'Test Description',
            'autoDef': {
                'sortField': 'date',
                'sortDirection': 'ASC',
                'keywordQuery': 'bikes',
            },
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testOPDS2Response'

            mockDB.createAutomaticCollection.assert_called_once_with(
                'Test Collection', 'Test Creator', 'Test Description',
                owner='testUser', sortField='date', sortDirection='ASC',
                limit=None, keywordQuery='bikes', authorQuery=None, titleQuery=None,
                subjectQuery=None,
            )
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with(newCollection, mockDB)

            mockBase64.assert_called_once_with(b'testAuth')

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                201, 'testOPDS2Feed'
            )

    def test_automaticCollectionCreate_invalid(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        testRequestBody = {
            'title': 'Test Collection',
            'creator': 'Test Creator',
            'description': 'Test Description',
            'autoDef': {
                'sortField': 'bad_sort_field',
                'keywordQuery': 'bikes',
            },
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testErrorResponse'

            mockDB.createAutomaticCollection.assert_not_called()
            mockUtils['formatResponseObject'].assert_called_once_with(
                400, "createCollection",
                {'message': "Invalid sort field bad_sort_field"},
            )

            mockBase64.assert_called_once_with(b'testAuth')

    def test_collectionCreate_invalid(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        testRequestBody = {
            'title': 'Test Collection',
            'creator': 'Test Creator',
            'description': 'Test Description',
            'editionIDs': [1, 2, 3],
            'autoDef': {
                'sortField': 'bad_sort_field',
                'keywordQuery': 'bikes',
            },
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testErrorResponse'

            mockDB.createAutomaticCollection.assert_not_called()
            mockUtils['formatResponseObject'].assert_called_once_with(
                400, "createCollection",
                {
                    'message': (
                        "Cannot create a collection with both an automatic collection "
                        "definition and editionIDs or workUUIDs"
                    ),
                },
            )

            mockBase64.assert_called_once_with(b'testAuth')

    def test_collectionCreate_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        testRequestBody = {
            'creator': 'Test Creator',
            'description': 'Test Description',
            'workUUIDs': ['uuid1', 'uuid2'],
            'editionIDs': ['ed1', 'ed2', 'ed3']
        }

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/',
            json=testRequestBody,
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionCreate()

            assert testAPIResponse == 'testErrorResponse'

            mockUtils['formatResponseObject'].assert_called_once_with(
                400,
                'createCollection',
                {
                    'message': 'title, creator and description fields are required',
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

    def test_collectionDelete_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.deleteCollection.return_value = 1

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionDelete('testUUID')

            assert testAPIResponse[0].status_code == 200
            assert testAPIResponse[0].json == {'message': 'Deleted testUUID'}

            assert mockDB.createSession.call_count == 2
            mockDB.deleteCollection.assert_called_once_with(
                'testUUID', 'testUser'
            )
            mockDB.session.commit.assert_called_once()

    def test_collectionDelete_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.deleteCollection.return_value = 0

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Bearer testToken'}
        ):
            testAPIResponse = collectionDelete('testUUID')

            assert testAPIResponse == 'testErrorResponse'

            assert mockDB.createSession.call_count == 2
            mockDB.deleteCollection.assert_called_once_with(
                'testUUID', 'testUser'
            )

            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'deleteCollection',
                {'message': 'No collection with UUID testUUID exists'}
            )

    def test_collectionDeleteWorkEdition_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        mockFeedConstruct = mocker.patch(
            'api.blueprints.drbCollection.constructOPDSFeed'
        )
        mockFeedConstruct.return_value = 'testOPDS2Feed'

        mockRemoveEdition = mocker.patch(
            'api.blueprints.drbCollection.removeWorkEditionsFromCollection'
        )

        mockUtils['formatOPDS2Object'].return_value = 'testOPDS2Response'

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/delete/testUUID?editionIDs=testID',
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionDeleteWorkEdition('testUUID')

            assert testAPIResponse == 'testOPDS2Response'

            assert mockDBClient.call_count == 2
            assert mockDB.createSession.call_count == 2
            assert mockRemoveEdition.call_count == 1
            mockDB.fetchSingleCollection.assert_called_once_with('testUUID')
            mockDB.session.commit.assert_called_once()

            mockFeedConstruct.assert_called_once_with(
                'testUUID', mockDB
            )

            mockUtils['formatOPDS2Object'].assert_called_once_with(
                200, 'testOPDS2Feed'
            )

    def test_collectionDeleteWorkEdition_error(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockDB.fetchSingleCollection\
            .return_value = mocker.MagicMock(uuid='testUUID')

        mockUtils['formatResponseObject'].return_value = 'testErrorResponse'

        mocker.patch.dict(os.environ, {'NYPL_API_CLIENT_PUBLIC_KEY': 'test'})

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/delete/testUUID',
            headers={'Authorization': 'Basic testAuth'}
        ):
            testAPIResponse = collectionDeleteWorkEdition('testUUID')

            assert testAPIResponse == 'testErrorResponse'

            assert mockDBClient.call_count == 1
            assert mockDB.createSession.call_count == 1

            mockUtils['formatResponseObject'].assert_called_once_with(
                400, 'deleteCollectionWorkEdition', {
                    'message':
                        'At least one of these fields(editionIDs & workUUIDs) are required'
                }
            )

    def test_collectionList_success(self, testApp, mockUtils, mocker):
        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        collections = [
            mocker.MagicMock(uuid="uuid1"), mocker.MagicMock(uuid="uuid2")
        ]
        mockDB.fetchCollections.return_value = collections

        mockFeed = mocker.MagicMock()
        mockFeedInit = mocker.patch('api.blueprints.drbCollection.Feed')
        mockFeedInit.return_value = mockFeed

        mockPaging = mocker.patch.object(OPDSUtils, 'addPagingOptions')

        mockConstruct = mocker.patch(
            'api.blueprints.drbCollection._constructOPDSFeedForCollection'
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
                mocker.call(collection, mockDB, perPage=5, path=f"/collection/{collection.uuid}")
                for collection in collections
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
        collection = mocker.MagicMock(
            uuid="testUUID",
            title='Test Collection',
            creator='Test Creator',
            description='Test Description',
            editions=[
                mocker.MagicMock(id=1), mocker.MagicMock(id=2)
            ],
            type="static",
        )
        mockDB.fetchSingleCollection.return_value = collection

        mocker.patch.dict(os.environ, {'ENVIRONMENT': 'test'})

        mockPaging = mocker.patch.object(OPDSUtils, 'addPagingOptions')

        mockSortCon = mocker.patch(
            'api.blueprints.drbCollection.constructSortMethod'
        )
        mockSortCon.return_value = (lambda x: str(x), False)

        with testApp.test_request_context('/collections/test'):
            testOPDSFeed = constructOPDSFeed(collection, mockDB, sort='test')

            assert testOPDSFeed == mockFeed

            mockFeed.addMetadata.assert_called_once_with({
                'title': 'Test Collection',
                'creator': 'Test Creator',
                'description': 'Test Description'
            })
            mockFeed.addLink.assert_called_once_with({
                'rel': 'self',
                'href': '/collection/testUUID',
                'type': 'application/opds+json'
            })
            mockFeed.addPublications.assert_called_once()

            assert mockPub.parseEditionToPublication.call_count == 2
            mockPub.addLink.assert_has_calls([
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/1',
                    'type': 'text/html',
                    'identifier': 'readable'
                }),
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/2',
                    'type': 'text/html',
                    'identifier': 'readable'
                })
            ])

            mockSortCon.assert_called_once_with('test')

            mockPaging.assert_called_once_with(
                mockFeed, '/collection/testUUID', 2, page=1, perPage=10
            )

    def test_constructOPDSFeed_success_autoCollection(self, testApp, mockUtils, mocker):
        mockFeed = mocker.MagicMock()
        mockFeedInit = mocker.patch('api.blueprints.drbCollection.Feed')
        mockFeedInit.return_value = mockFeed

        mockPub = mocker.MagicMock()
        mockPubInit = mocker.patch('api.blueprints.drbCollection.Publication')
        mockPubInit.return_value = mockPub

        mockDB = mocker.MagicMock()
        collection = mocker.MagicMock(
            uuid="testUUID",
            title='Test Collection',
            creator='Test Creator',
            description='Test Description',
            type="automatic",
        )
        mockDB.fetchSingleCollection.return_value = collection
        mockES = mocker.MagicMock()

        mocker.patch(
            "api.blueprints.drbCollection.fetchAutomaticCollectionEditions",
            return_value=(
                mocker.sentinel.totalCount,
                [mocker.MagicMock(id=1), mocker.MagicMock(id=2)],
            ),
        )

        mocker.patch.dict(
            os.environ,
            {'ENVIRONMENT': 'test', 'ELASTICSEARCH_INDEX': 'test_es_index'},
        )
        testApp.config['REDIS_CLIENT'] = 'test_redis_client'

        mockPaging = mocker.patch.object(OPDSUtils, 'addPagingOptions')

        with testApp.test_request_context('/collections/test'):
            testOPDSFeed = constructOPDSFeed(collection, mockDB, sort='test')

            assert testOPDSFeed == mockFeed

            mockFeed.addMetadata.assert_called_once_with({
                'title': 'Test Collection',
                'creator': 'Test Creator',
                'description': 'Test Description'
            })
            mockFeed.addLink.assert_called_once_with({
                'rel': 'self',
                'href': '/collection/testUUID',
                'type': 'application/opds+json'
            })
            mockFeed.addPublications.assert_called_once()

            assert mockPub.parseEditionToPublication.call_count == 2
            mockPub.addLink.assert_has_calls([
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/1',
                    'type': 'text/html',
                    'identifier': 'readable'
                }),
                mocker.call({
                    'rel': 'alternate',
                    'href': 'https://drb-qa.nypl.org/edition/2',
                    'type': 'text/html',
                    'identifier': 'readable'
                })
            ])

            mockPaging.assert_called_once_with(
                mockFeed, '/collection/testUUID', mocker.sentinel.totalCount, page=1, perPage=10
            )

    def test_validateToken_success(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = True

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Basic testAuth'}
        ):
            decoratedFunction()

            mockBase64.assert_called_once_with(b'testAuth')

            mockFunc.assert_called_once_with(user='testUser')

    def test_validateToken_error_no_header(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context('/'):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                403, 'authResponse',
                {'message': 'user/password not provided'}
            )

    def test_validateToken_error_auth(self, testApp, mockUtils, mocker):
        mockFunc = mocker.MagicMock()

        decoratedFunction = validateToken(mockFunc)

        mockDB = mocker.MagicMock(session=mocker.MagicMock())
        mockDBClient = mocker.patch('api.blueprints.drbCollection.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchUser.return_value = mocker.MagicMock(
            user='testUser', password='testPswd', salt='testSalt'
        )

        mockBase64 = mocker.patch('api.blueprints.drbCollection.b64decode')
        mockBase64.return_value = b'testUser:testPswd'

        mockUtils['validatePassword'].return_value = False

        mockUtils['formatResponseObject'].return_value = 'testError'

        with testApp.test_request_context(
            '/', headers={'Authorization': 'Basic testAuth'}
        ):
            testResponse = decoratedFunction()

            assert testResponse == 'testError'

            mockUtils['formatResponseObject'].assert_called_once_with(
                401, 'authResponse',
                {'message': 'invalid user/password'}
            )
