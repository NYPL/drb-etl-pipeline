from io import BytesIO
import json
import os
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials

SERVICE_ACCOUNT_FILE = os.environ['GOOGLE_SERVICE_ACCOUNT_FILE']

def create_drive_service(service_account_info):
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_info(service_account_info, scopes=scopes)

    return build('drive', 'v3', credentials=credentials)

def get_drive_file(file_id: str) -> BytesIO:
    drive_service = create_drive_service(service_account_info=json.loads(SERVICE_ACCOUNT_FILE))
    request = drive_service.files().get_media(fileId=file_id)
    file = BytesIO()

    try:
        downloader = MediaIoBaseDownload(file, request)

        done = False
        while done is False:
            status, done = downloader.next_chunk()
            print(f"Download {int(status.progress() * 100)}.")

    except HttpError as error:
        print(f"An error occurred when downloading Drive file {file_id}: {error}")
        file = None

    return file






