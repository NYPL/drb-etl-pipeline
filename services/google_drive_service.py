from io import BytesIO
import json
import os
from typing import Optional
from urllib.parse import urlparse, parse_qs
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials
from services.ssm_service import get_parameter


from logger import create_log

logger = create_log(__name__)

<<<<<<< HEAD
def _create_drive_service():
    if os.environ['ENVIRONMENT'] == 'production':
        SERVICE_ACCOUNT_FILE = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/google-drive-service-key')
        pass
    else:
        SERVICE_ACCOUNT_FILE = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/google-drive-service-key')
    service_account_info = json.loads(SERVICE_ACCOUNT_FILE)
    scopes = ['https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata']
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)
    drive_service = build('drive', 'v3', credentials=credentials)
    return drive_service

drive_service = None

def _get_or_create_drive_service():
    if drive_service is not None:
        return drive_service
    drive_service = _create_drive_service()
    return drive_service

def get_drive_file(file_id: str) -> Optional[BytesIO]:
    request = _get_or_create_drive_service().files().get_media(fileId=file_id)
    file = BytesIO()
=======
class GoogleDriveService:
    def __init__(self):
        if os.environ['ENVIRONMENT'] == 'production':
            SERVICE_ACCOUNT_FILE = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/production/google-drive-service-key')
        else:
            SERVICE_ACCOUNT_FILE = get_parameter('arn:aws:ssm:us-east-1:946183545209:parameter/drb/qa/google-drive-service-key')
        self.service_account_info = json.loads(SERVICE_ACCOUNT_FILE)
        self.scopes = ['https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive.metadata']
        self.credentials = Credentials.from_service_account_info(self.service_account_info, scopes=self.scopes)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)

    def get_drive_file(self, file_id: str) -> Optional[BytesIO]:
        request = self.drive_service.files().get_media(fileId=file_id)
        file = BytesIO()

        try:
            downloader = MediaIoBaseDownload(file, request)
>>>>>>> Drive-refactor-as-class

            done = False
            while not done:
                status, done = downloader.next_chunk()

        except HttpError as error:
            logger.warning(f"HTTP error occurred when downloading Drive file {file_id}: {error}")
            return None
        except Exception as err:
            logger.exception(f"Error occurred when downloading Drive file {file_id}")
            return None

        return file

<<<<<<< HEAD
    return file

def get_file_metadata(file_id: str) -> Optional[str]:
    request = _get_or_create_drive_service.files().get(fileId=file_id, supportsAllDrives=True)
    meta = request.execute()
    return meta

def id_from_url(url: str) -> Optional[str]:
    return parse_qs(urlparse(url).query)['id'][0]
=======
    def get_file_metadata(self, file_id: str) -> Optional[str]:
        # supportsAllDrives=True required as of 12/24 despite deprecation
        request = self.drive_service.files().get(fileId=file_id, supportsAllDrives=True)
        meta = request.execute()
        return meta

    @staticmethod
    def id_from_url(url: str) -> Optional[str]:
        return parse_qs(urlparse(url).query)['id'][0]
>>>>>>> Drive-refactor-as-class
