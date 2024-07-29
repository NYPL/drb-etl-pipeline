from datetime import datetime, timezone
import os
import requests
from requests.exceptions import Timeout, ConnectionError
import time

from logger import createLog


logger = createLog(__name__)


class OCLCAuthManager:
    _token = None
    _token_expires_at = None
    OCLC_AUTH_URL = 'https://oauth.oclc.org/token?scope=wcapi&grant_type=client_credentials'
    TIME_TO_REFRESH_IN_SECONDS = 60
    

    @classmethod
    def getToken(cls):
        OCLC_CLIENT_ID = os.environ.get('OCLC_CLIENT_ID', None)
        OCLC_CLIENT_SECRET = os.environ.get('OCLC_CLIENT_SECRET', None)

        if cls._token and cls._token_expires_at:
            expiry_date = datetime.strptime(cls._token_expires_at, "%Y-%m-%d %H:%M:%SZ")
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            time_to_expiry_in_seconds = (expiry_date - now).total_seconds()

            print(time_to_expiry_in_seconds)
            
            if time_to_expiry_in_seconds > cls.TIME_TO_REFRESH_IN_SECONDS:
                return cls._token
            
        try:
            authResp = requests.post(
                cls.OCLC_AUTH_URL,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                auth=(OCLC_CLIENT_ID, OCLC_CLIENT_SECRET),
            )
        except (Timeout, ConnectionError):
            logger.warning(f'Failed to retrieve token from {cls.OCLC_AUTH_URL}')
            return None

        if authResp.status_code != 200:
            logger.warning(f'OCLC token retrieval failed with status {authResp.status_code}')
            return None

        authData = authResp.json()
        cls._token = authData['access_token']
        cls._token_expires_at = authData['expires_at']

        return cls._token
