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
            formatResponseObject=mocker.DEFAULT,
            generate_presigned_url=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')

        return flaskApp
    
    def test_s3ObjectLinkFetch_success(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'
        mockUtils['generate_presigned_url'].return_value = 'https://digital-research-books-beta.nypl.org/work/2263dbf4-51c2-4f6e-b9eb-e1def96b48d4?featured=9401263'


        with testApp.test_request_context('/?key=manifests/met/10935.json'):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qa')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(
                200, 's3ObjectLinkFetch', {'message': 'https://digital-research-books-beta.nypl.org/work/2263dbf4-51c2-4f6e-b9eb-e1def96b48d4?featured=9401263'}
            )

    def test_s3ObjectLinkFetch_fail(self, mockUtils, testApp, mocker):

        mockUtils['normalizeQueryParams'].return_value = {'key': ['manifests/met/10935.json']}
        mockUtils['formatResponseObject'].return_value = 'testS3Response'
        mockUtils['generate_presigned_url'].return_value = 'https://drb-files-qaFail.s3.amazonaws.com/manifests/met/10935.json?'

        with testApp.test_request_context('/?key=manifests/met/10935.json'):
            testAPIResponse = s3ObjectLinkFetch('drb-files-qaFail')

            assert testAPIResponse == 'testS3Response'

            mockUtils['normalizeQueryParams'].assert_called_once_with(ImmutableMultiDict([('key', 'manifests/met/10935.json')]))

            mockUtils['formatResponseObject'].assert_called_once_with(404, 's3ObjectLinkFetch', {'Bucket/Key does not exist': 'https://drb-files-qaFail.s3.amazonaws.com/manifests/met/10935.json?'})