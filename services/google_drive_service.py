from io import BytesIO
import json
import os
from typing import Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = os.environ['GOOGLE_SERVICE_ACCOUNT_FILE']

from logger import create_log

logger = create_log(__name__)

service_account_info = json.loads(SERVICE_ACCOUNT_FILE)
scopes = ['https://www.googleapis.com/auth/drive']
credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)

drive_service = build('drive', 'v3', credentials=credentials)

def get_drive_file(file_id: str) -> Optional[BytesIO]:
    request = drive_service.files().get_media(fileId=file_id)
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
