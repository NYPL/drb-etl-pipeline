import os
import io
import boto3
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from google.oauth2.service_account import Credentials

s3 = boto3.client('s3')

def create_drive_service(service_account_file):
    scopes = ['https://www.googleapis.com/auth/drive']
    credentials = Credentials.from_service_account_file(service_account_file, scopes=scopes)
    return build('drive', 'v3', credentials=credentials)

def upload_to_google_drive(service, folder_id, file_name, file_data):
    media = MediaIoBaseUpload(io.BytesIO(file_data), mimetype='application/octet-stream')
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    return file.get('id')

def s3_to_google_drive(s3_bucket, google_folder_id, service_account_file):
    drive_service = create_drive_service(service_account_file)
    
    response = s3.list_objects_v2(Bucket=s3_bucket)
    if 'Contents' not in response:
        print(f"No files found in S3 bucket {s3_bucket}")
        return

    for obj in response['Contents']:
        file_key = obj['Key']
        print(f"Processing file: {file_key}")
        
        s3_object = s3.get_object(Bucket=s3_bucket, Key=file_key)
        file_data = s3_object['Body'].read()
        
        try:
            drive_file_id = upload_to_google_drive(drive_service, google_folder_id, file_key, file_data)
            print(f"Uploaded {file_key} to Google Drive with ID: {drive_file_id}")
        except Exception as e:
            print(f"Failed to upload {file_key} to Google Drive: {e}")

if __name__ == "__main__":
    S3_BUCKET_NAME = "ump-pdfs"
    GOOGLE_DRIVE_FOLDER_ID = "drive_folder_id"
    SERVICE_ACCOUNT_FILE = "scripts/auth/service-account.json"

    s3_to_google_drive(S3_BUCKET_NAME, GOOGLE_DRIVE_FOLDER_ID, SERVICE_ACCOUNT_FILE)
