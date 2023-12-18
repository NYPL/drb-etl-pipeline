from flask import Flask
import pytest

import jwt

from api.blueprints.drbFulfill import workFulfill
from api.utils import APIUtils


class TestSearchBlueprint:
    @pytest.fixture
    def mockUtils(self, mocker):
        return mocker.patch.multiple(
            APIUtils,
            formatResponseObject=mocker.DEFAULT
        )

    @pytest.fixture
    def testApp(self):
        flaskApp = Flask('test')
        flaskApp.config['DB_CLIENT'] = 'testDBClient'
        flaskApp.config['READER_VERSION'] = 'test'

        return flaskApp
    
    def test_workFulfill_expired_token(self, testApp, mockUtils, monkeypatch):
        monkeypatch.setenv('NYPL_API_CLIENT_PUBLIC_KEY', "cat")
        expiredKey = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyLCJleHAiOjE3MDAwMDAwMDB9.u_NAqhUTudJP2vdZZWZ8fMZchyb65H1wOnYWQ98mWHCb8Q2IZXX4Siglh90JtAWTn1zkSygrpij6dDNWlwtQ-RP9eOOwe7-vAXrpEg1BJVM0Q08WCATJArQoygpjK7mLgTz6LLsb4D3QsXr1J7w9tWI_L5ybc8Z4d-vsp4-vCOptB7x21Q_3ZreDnQouPwv7tfQvpqlgYPCPRf7ekmeNAmHsfo1z0IXdlIhuWlw4fYZ5NZJNWjy0dSbn9CsOGALgKi5cbYxBu9bPMGAnEfEXzc-cYu5FDkT53FDLFypjTjR7L4QQRmykVIBBD2d5ZUGv0Jr_-GCnhMIh66WD4Pmhv4jIoh8MgcxjY18PMcP0IxSq1eJOx7O_Td-t4-8S1a_az1Qi15LH7ThQ8K63SUYA3L4EfXU5Uqw_xZmq8E5zceyzUOEdsPrSU3wyL2dpRVokN0dBBofnoem6Dne0HASQg9BHzclF5I7VByla88efgeS0ovoseA4kn3w1wBu7T-069RxGxTMwR5ddlaJc-UVp-hy3N_38Z0pUqZUXsJDmaoDyaWNSM5odhAaWrDUxlZy7r9CGHnr_PAZy2c46sx-An7cQa62Ir2Q-8I13W4CeMvYJcgC6IHVlmf10IugdN7WnVp2vzWC77vO08RCYLUMA8ekMcaKGs8r1bx7OtY4_5ss"
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': expiredKey}):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                401, 'fulfill', 'Expired access token'
            )

    def test_workFulfill_invalid_token(self, testApp, mockUtils, monkeypatch):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': 'Bearer Whatever'}):
            monkeypatch.setenv('NYPL_API_CLIENT_PUBLIC_KEY', "SomeKeyValue")
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_no_bearer_auth(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': 'Whatever'}):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_empty_token(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345', 
                                          headers={'Authorization': ''}):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')

    def test_workFulfill_no_header(self, testApp, mockUtils):
        with testApp.test_request_context('/fulfill/12345'):
            workFulfill('12345')
            mockUtils['formatResponseObject'].assert_called_once_with(
                    401, 'fulfill', 'Invalid access token')
        

    