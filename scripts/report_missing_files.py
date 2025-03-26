import botocore
import json
import requests
from multiprocessing import Pool, Value, Lock
import sys

from managers import DBManager, S3Manager
from model import Part, Record


'''
Usage:  python main.py --script ReportMissingFiles -e <env> options source=<source>
'''

record_count = Value('i', 0)
missing_file_count = Value('i', 0)
lock = Lock()


def is_record_missing_files(record_parts: tuple) -> bool:
    s3_manager = S3Manager()
    s3_manager.createS3Client()

    parts, *_ = record_parts

    for part in parts:
        index, url, source, file_type, flags = part.split('|')
        file_part = Part(index, url, source, file_type, flags)
        
        if json.loads(file_part.flags).get('cover') == True:
            continue

        if file_part.file_bucket:
            try:
                s3_manager.s3Client.head_object(Bucket=file_part.file_bucket, Key = file_part.file_key)
            except botocore.exceptions.ClientError:
                return True
        else:
            try:
                url_head_response = requests.head(url)

                if not url_head_response.ok:
                    print(f'Received {url_head_response.status_code} for url: {url}')
                    return True
            except Exception:
                return True
            
    return False


def main(*args):
    db_manager = DBManager()
    db_manager.createSession()

    source_arg = next((option for option in args if option.startswith('source=')), None)
    source = source_arg.split('=')[1] if source_arg else 'gutenberg'

    record_parts = db_manager.session.query(Record.has_part).filter(Record.source == source).all()

    def track_progress(is_missing_file):
        with lock:
            record_count.value += 1
            if is_missing_file:
                missing_file_count.value += 1
            
            print(f'{source} records with missing files: {missing_file_count.value}/{record_count.value} - total: {len(record_parts)}', end='\r', flush=True)

    with Pool(processes=8) as pool:
        for is_missing_file in pool.imap_unordered(is_record_missing_files, record_parts):
            track_progress(is_missing_file)

    print(f'{source} records with missing files: {missing_file_count.value}/{len(record_parts)}')

if __name__ == '__main__':
    args = sys.argv[1:]
    main(*args)
