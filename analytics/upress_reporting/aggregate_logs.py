import argparse
import boto3
from datetime import datetime, date, timedelta
import os
import sys

from main import load_env_file


def parse_args(args):
    parser = argparse.ArgumentParser(prog='Aggregate logs script arguments')
    
    parser.add_argument('--start', '-s', help='starting date in the format yyyy-mm-dd')
    parser.add_argument('--end', '-e', help='end date in the format yyyy-mm-dd')
    
    return parser.parse_args(args)


def aggregate_logs(bucket_name: str, file_path: str, folder_name: str):
    download_folder = f'analytics/upress_reporting/log_files/{bucket_name}/{folder_name}'
    os.system(f'aws s3 cp --recursive s3://{bucket_name}/{file_path}{folder_name} {download_folder}')

    folder_directory = os.fsencode(download_folder)
    aggregated_log_file = f'analytics/upress_reporting/log_files/{bucket_name}/{folder_name}/aggregated_log'

    for file in os.listdir(folder_directory):
        if file == aggregated_log_file: continue

        filename = os.fsdecode(file)
        
        with open(aggregated_log_file, 'a') as aggregated_log:
            with open(f'{download_folder}/{filename}', 'r') as log_file:
                for line in log_file:
                    # TODO: filter lines that don't matter
                    aggregated_log.write(line)

    # TODO: upload back to S3 and delete files


def main():
    load_env_file('local-qa', file_string='config/local-qa.yaml')
    
    view_bucket = os.getenv('VIEW_BUCKET')
    view_log_path = os.getenv('VIEW_LOG_PATH')
    download_bucket = os.getenv('DOWNLOAD_BUCKET')
    download_bucket_path = os.getenv('DOWNLOAD_LOG_PATH')

    parsed_args = parse_args(sys.argv[1:])

    start_date = datetime.strptime(parsed_args.start, '%Y-%m-%d').date()
    end_date = datetime.strptime(parsed_args.end, '%Y-%m-%d').date()

    while start_date <= end_date:
        folder_name = start_date.strftime('%Y/%m/%d')

        aggregate_logs(view_bucket, view_log_path, folder_name)
        aggregate_logs(download_bucket, download_bucket_path, folder_name)

        start_date += timedelta(days=1)


if __name__ == '__main__':
    main()
