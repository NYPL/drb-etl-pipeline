from datetime import datetime, timezone
import os
import requests
from requests.exceptions import Timeout, ConnectionError

from logger import createLog


logger = createLog(__name__)


class OCLCAuthManager:
    _token = None
    _token_expires_at = None
    OCLC_AUTH_URL = 'https://oauth.oclc.org/token?scope=wcapi&grant_type=client_credentials'
    TIME_TO_REFRESH_IN_SECONDS = 60
    

    @classmethod
    def get_token(cls):
        OCLC_CLIENT_ID = os.environ.get('OCLC_CLIENT_ID', None)
        OCLC_CLIENT_SECRET = os.environ.get('OCLC_CLIENT_SECRET', None)

        if cls._token and cls._token_expires_at:
            expiry_date = datetime.strptime(cls._token_expires_at, "%Y-%m-%d %H:%M:%SZ")
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            time_to_expiry_in_seconds = (expiry_date - now).total_seconds()
            
            if time_to_expiry_in_seconds > cls.TIME_TO_REFRESH_IN_SECONDS:
                return cls._token
            
        try:
            auth_response = requests.post(
                cls.OCLC_AUTH_URL,
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                auth=(OCLC_CLIENT_ID, OCLC_CLIENT_SECRET),
            )
        except (Timeout, ConnectionError):
            logger.warning(f'Failed to retrieve token from {cls.OCLC_AUTH_URL}')
            return None

        if auth_response.status_code != 200:
            logger.warning(f'OCLC token retrieval failed with status {auth_response.status_code}')
            return None

        auth_data = auth_response.json()
        cls._token = auth_data['access_token']
        cls._token_expires_at = auth_data['expires_at']

        return cls._token
