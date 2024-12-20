from io import BytesIO
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials


from logger import create_log

logger = create_log(__name__)

def create_drive_service():
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

def get_or_create_drive_service():
    if drive_service is not None:
        return drive_service
    drive_service = create_drive_service()
    return drive_service

def get_drive_file(file_id: str) -> Optional[BytesIO]:
    request = get_or_create_drive_service().files().get_media(fileId=file_id)
    file = BytesIO()

    try:
        downloader = MediaIoBaseDownload(file, request)

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
