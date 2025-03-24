import botocore
import requests
import sys

from managers import DBManager, S3Manager
from model import Part, Record


'''
Usage:  python main.py --script ReportFileAccessibility -e <env> options source=<source>
'''
def main(*args):
    db_manager = DBManager()
    db_manager.createSession()

    s3_manager = S3Manager()
    s3_manager.createS3Client()

    source_arg = next(filter(lambda option: option.startswith('source'), args), None)
    source = source_arg.split('=')[1] if source_arg else 'gutenberg'

    record_parts = db_manager.session.query(Record.has_part, Record.source_id).filter(Record.source == source).yield_per(1000)

    records_with_missing_files = 0
    record_count = 0

    for record_count, (parts, source_id, *_) in enumerate(record_parts, 1):
        for part in parts:
            index, url, source, file_type, flags = part.split('|')
            file_part = Part(index, url, source, file_type, flags)

            if file_part.file_bucket:
                try:
                    s3_manager.s3Client.head_object(Bucket=file_part.file_bucket, Key = file_part.file_key)
                except botocore.exceptions.ClientError:
                    print(f'{source_id} is missing a file: {file_part}')
                    records_with_missing_files += 1
                    break
            else:
                requests.head(url)
                
    print(f'Percentage of {source} records with missing files: {(records_with_missing_files / record_count) * 100}%')

if __name__ == '__main__':
    args = sys.argv[1:]
    main(*args)
