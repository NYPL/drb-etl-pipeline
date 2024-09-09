import argparse
from datetime import datetime, timedelta
import os
import re
import shutil
import sys

from main import load_env_file


def parse_args(args):
    parser = argparse.ArgumentParser(prog='Aggregate logs script arguments')
    
    parser.add_argument('--start', '-s', help='starting date in the format yyyy-mm-dd')
    parser.add_argument('--end', '-e', help='end date in the format yyyy-mm-dd')
    
    return parser.parse_args(args)


def aggregate_logs(bucket_name: str, file_path: str, folder_name: str, file_id_regex: str):
    download_folder = f'analytics/upress_reporting/log_files/{bucket_name}/{folder_name}'
    os.system(f'aws s3 cp --recursive s3://{bucket_name}/{file_path}{folder_name} {download_folder}')

    folder_directory = os.fsencode(download_folder)
    aggregated_log_file = f'analytics/upress_reporting/log_files/{bucket_name}/{folder_name}/aggregated_log'

    for file in os.listdir(folder_directory):
        if file == aggregated_log_file: 
            continue

        filename = os.fsdecode(file)
        
        with open(aggregated_log_file, 'a') as aggregated_log:
            with open(f'{download_folder}/{filename}', 'r') as log_file:
                for line in log_file:
                    match_file_id = re.search(file_id_regex, line)
                    match_referrer = re.search(os.getenv('REFERRER_URL'), line)

                    if not match_file_id or not match_referrer or "403 AccessDenied" in line:
                        continue

                    aggregated_log.write(line)
            
            os.remove(f'{download_folder}/{filename}')


def main():
    load_env_file('local-qa', file_string='config/local-qa.yaml')
    
    view_bucket = os.getenv('VIEW_BUCKET')
    view_log_path = os.getenv('VIEW_LOG_PATH')
    download_bucket = os.getenv('DOWNLOAD_BUCKET')
    download_bucket_path = os.getenv('DOWNLOAD_LOG_PATH')

    parsed_args = parse_args(sys.argv[1:])

    start_date = datetime.strptime(parsed_args.start, '%Y-%m-%d').date()
    end_date = datetime.strptime(parsed_args.end, '%Y-%m-%d').date()

    shutil.rmtree('analytics/upress_reporting/log_files', ignore_errors=True)

    while start_date <= end_date:
        folder_name = start_date.strftime('%Y/%m/%d')

        aggregate_logs(view_bucket, view_log_path, folder_name, r"REST.GET.OBJECT manifests/(.*?json)\s")
        aggregate_logs(download_bucket, download_bucket_path, folder_name, r"REST.GET.OBJECT (.+pdf\s)")

        start_date += timedelta(days=1)


if __name__ == '__main__':
    main()
