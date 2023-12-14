from flask import Flask
import pytest

from api.blueprints.drbS3 import s3ObjectLinkFetch
from api.utils import APIUtils

from werkzeug.datastructures import ImmutableMultiDict 

class TestS3Blueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            normalizeQueryParams=mocker.DEFAULT,
            formatResponseObject=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')

        return flaskApp
    
    def test_s3ObjectLinkFetch_success(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'


        with testApp.test_request_context('/?key=manifests/met/10935.json'):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qa')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 's3ObjectLinkFetch', {'message': f'Object URL: https://drb-files-qa.s3.amazonaws.com/manifests/met/10935.json'}
            )

    def test_s3ObjectLinkFetch_fail(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'
    

        with testApp.test_request_context('/?key=manifests/met/10935.json'):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qaFail')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(
                404, 's3ObjectLinkFetch', {'message': f'URL does not exist https://drb-files-qaFail.s3.amazonaws.com/manifests/met/10935.json'}
            )
