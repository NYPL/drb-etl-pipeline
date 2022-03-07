from flask import Flask
import pytest
from datetime import date

from api.blueprints.drbCitation import citationFetch
from api.utils import APIUtils


class TestCitationBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT,
            normalizeQueryParams=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'

        return flaskApp

# Tests for when work uuid and format values are set correctly

    #* Bible work before 1900 successful test
    def test_citationFetch_bible_pre1900_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
            mockDBClient.return_value = mockDB

            editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace')]

            mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='The Bible', editions=editionMocks)
            
            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/?format=mla'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': 'The Bible. Unknown version, testPubPlace, 1800.'}
                )

    #* Bible work after 1900 successful test
    def test_citationFetch_bible_post1900_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
            mockDBClient.return_value = mockDB

            editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}])]

            mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='The Bible', editions=editionMocks)
            
            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/?format=mla'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': 'The Bible. Unknown version, NYPL, 2022.'}
                )

    #* Government work successful test
    def test_citationFetch_post1900_gov_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
            mockDBClient.return_value = mockDB

            editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}], \
                            measurements = [{'type': 'government_document', 'value': '1'}])]

            mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='State of the Union Address', \
                                                authors=[{'name': 'United States. Test Agency'}], \
                                                editions = editionMocks) \
                                                
            
            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/?format=mla'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': ' '.join('United States, Test Agency. State of the Union Address. \
                                    NYPL, 2022.'.split())}
                )

    #* Translated work prepared by an editor successful test
    def test_citationFetch_no_author_pre1900_trans_editor_success(self, mockUtils, testApp, mocker):
            mockDB = mocker.MagicMock()
            mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
            mockDBClient.return_value = mockDB

            editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                            measurements = [{'type': 'government_document', 'value': '0'}])]

            mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                                contributors = [{'roles': 'translator', 'name': 'transLastName, transFirstName'}, \
                                                {'roles': 'editor', 'name': 'editLastName, editFirstName'}], \
                                                editions = editionMocks) 
                                                
            
            mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

            with testApp.test_request_context('/?format=mla'):
                testAPIResponse = citationFetch('testUUID')

                assert testAPIResponse == 'citationResponse'
                mockDBClient.assert_called_once_with('testDBClient')

                mockUtils['normalizeQueryParams'].assert_called_once()

                mockUtils['formatResponseObject'].assert_called_once_with(
                    200, 'citation', {'mla': ' '.join('testTitle. Translated by transFirstName \
                                    transLastName, edited by editFirstName editLastName, \
                                    testPubPlace, 1800.'.split())}
                )

    #* Translated work not prepared by editor successful test
    def test_citationFetch__no_author_pre1900_trans_success(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            contributors = [{'roles': 'translator', 'name': 'transLastName, transFirstName'}], \
                                            editions = editionMocks) 
                                                
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testTitle. Translated by transFirstName \
                                transLastName, \
                                testPubPlace, 1800.'.split())}
                )
    
    #* Single edition work successful test
    def test_citationFetch__no_author_pre1900_single_edit_work_success(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                        edition_statement = None, measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            editions = editionMocks) 
                                                
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testTitle. \
                                testPubPlace, 1800.'.split())}
                )

    #* Multiple edition work successful test
    def test_citationFetch_no_author_post1900_mult_edit_success(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}], \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', edition_statement = '2nd edition.', \
                                            editions = editionMocks)           
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testTitle. 2nd edition., \
                                NYPL, 2022.'.split())}
                )

    #* Test 1 for work with one author
    def test_citationFetch__one_author_work(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            authors = [{'name': 'testLastName, testFirstName'}], \
                                            contributors = [{'roles': 'editor', 'name': 'editLastName, editFirstName'}], \
                                            editions = editionMocks) 
                                                
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName. testTitle, \
                                edited by editFirstName editLastName, \
                                testPubPlace, 1800.'.split())}
                )
    
    #* Test 2 for work with one author
    def test_citationFetch_one_author_work2(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}], \
                        edition_statement = None, measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            authors = [{'name': 'testLastName, testFirstName'}], \
                                            editions = editionMocks) 
                                                
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName. testTitle. \
                                NYPL, 2022.'.split())}
                )

    #* Test 1 for work with two authors
    def test_citationFetch__two_author_work(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            authors = [{'name': 'testLastName, testFirstName'}, \
                                            {'name': 'testLastName2, testFirstName2'}], \
                                            contributors = [{'roles': 'editor', 'name': 'editLastName, editFirstName'}], \
                                            editions = editionMocks) 
                                                
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName, and testFirstName2 testLastName2. \
                                testTitle, edited by editFirstName editLastName, \
                                testPubPlace, 1800.'.split())}
                )
    
    #* Test 2 for works with two authors
    def test_citationFetch_two_authors_work2(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}], \
                        edition_statement = '2nd edition.', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', authors = [{'name': 'testLastName, testFirstName'}, \
                                            {'name': 'testLastName2, testFirstName2'}], \
                                            editions = editionMocks)           
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName, and testFirstName2 testLastName2. \
                                testTitle. 2nd edition., \
                                NYPL, 2022.'.split())}
                )

    #* Test 1 for work with three authors
    def test_citationFetch__three_authors_work(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(1800, 1, 1), publication_place='testPubPlace', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', \
                                            authors = [{'name': 'testLastName, testFirstName'}, \
                                            {'name': 'testLastName2, testFirstName2'}, \
                                            {'name': 'testLastName3, testFirstName3'}], \
                                            contributors = [{'roles': 'editor', 'name': 'editLastName, editFirstName'}], \
                                            editions = editionMocks) 
                                                
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName, et al. \
                                testTitle, edited by editFirstName editLastName, \
                                testPubPlace, 1800.'.split())}
                )
    
    #* Test 2 for works with three authors
    def test_citationFetch_three_authors_work2(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        editionMocks = [mocker.MagicMock(publication_date=date(2022, 1, 1), publishers=[{'name': 'NYPL'}], \
                        edition_statement = '2nd edition.', \
                        measurements = [{'type': 'government_document', 'value': '0'}])]

        mockDB.fetchSingleWork.return_value = mocker.MagicMock(title='testTitle', authors = [{'name': 'testLastName, testFirstName'}, \
                                            {'name': 'testLastName2, testFirstName2'}, \
                                            {'name': 'testLastName3, testFirstName3'}], \
                                            editions = editionMocks)           
            
        mockUtils['formatResponseObject'].return_value\
                = 'citationResponse'

        with testApp.test_request_context('/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == 'citationResponse'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 'citation', {'mla': ' '.join('testLastName, testFirstName, et al. \
                                testTitle. 2nd edition., \
                                NYPL, 2022.'.split())}
                )

    #Test for when the work uuid is not avaliable 
    def test_citationFetch_fail(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        mockDB.fetchSingleWork.return_value = None

        mockUtils['formatResponseObject'].return_value = '404Response'

        with testApp.test_request_context('testUUID/?format=mla'):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == '404Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatResponseObject'].assert_called_once_with(
                404,
                'citation',
                {'message': 'Unable to locate work with UUID testUUID'}
            )

    #Test for when request arguments for format are not set
    def test_citationFetch_fail2(self, mockUtils, testApp, mocker):
        mockDB = mocker.MagicMock()
        mockDBClient = mocker.patch('api.blueprints.drbCitation.DBClient')
        mockDBClient.return_value = mockDB

        mockUtils['formatResponseObject'].return_value = '400Response'

        with testApp.test_request_context('/?format='):
            testAPIResponse = citationFetch('testUUID')

            assert testAPIResponse == '400Response'
            mockDBClient.assert_called_once_with('testDBClient')

            mockUtils['normalizeQueryParams'].assert_called_once()
            mockUtils['formatResponseObject'].assert_called_once_with(
                400,
                'pageNotFound',
                {'message': 'Need to specify citation format'}
            )