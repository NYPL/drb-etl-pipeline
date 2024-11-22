import io
import boto3
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

# Please install the requirements with this command: pip install boto3 google-api-python-client google-auth

s3 = boto3.client('s3')

S3_BUCKET = 'ump-pdf-repository'
SERVICE_ACCOUNT_FILE = 'service-account.json'
FOLDER_ID = '1gRgJiPWnFhMu56KL8bKorHepF1BLElOL'


def create_drive_service(service_account_file):
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    
    return build('drive', 'v3', credentials=credentials)


def upload_to_google_drive(file_name, file_data):
    drive_service = create_drive_service(service_account_file=SERVICE_ACCOUNT_FILE)
    
    file = drive_service.files().create(
        body={ 'name': file_name, 'parents': [FOLDER_ID] },
        media_body=MediaIoBaseUpload(io.BytesIO(file_data), mimetype='application/octet-stream'),
        supportsAllDrives=True,
        fields='id'
    ).execute()
    
    return file.get('id')


def move_s3_files_to_google_drive(s3_bucket):
    list_objects_response = s3.list_objects_v2(Bucket=s3_bucket)
    
    if 'Contents' not in list_objects_response:
        print(f'No files found in S3 bucket {s3_bucket}')
        return

    for object in list_objects_response['Contents']:
        file_key = object['Key']
        print(f'Processing file: {file_key}')
        
        s3_object = s3.get_object(Bucket=s3_bucket, Key=file_key)
        file_data = s3_object['Body'].read()
        
        try:
            drive_file_id = upload_to_google_drive(file_key, file_data)
            print(f'Uploaded {file_key} to Google Drive with ID: {drive_file_id}')
        except Exception as e:
            print(f'Failed to upload {file_key} to Google Drive: {e}')


if __name__ == '__main__':
    move_s3_files_to_google_drive(S3_BUCKET)
