import os
import re
import pandas
import shutil


def aggregate_logs_in_day(s3_bucket: str, s3_path: str, folder_name: str,
                          file_id_regex: str, referrer_url: str):
    LOG_PATH = os.environ.get("AGGREGATED_LOG_PATH", None)
    download_folder = f"{LOG_PATH}{s3_bucket}/{folder_name}"
    os.system(
        f"aws s3 cp --recursive s3://{s3_bucket}/{s3_path}{folder_name} {download_folder}")

    folder_directory = os.fsencode(download_folder)
    aggregated_log_file = f"{LOG_PATH}{s3_bucket}/{folder_name}/aggregated_log"

    for file in os.listdir(folder_directory):
        if file == aggregated_log_file:
            continue

        filename = os.fsdecode(file)

        with open(aggregated_log_file, 'a') as aggregated_log:
            with open(f'{download_folder}/{filename}', 'r') as log_file:
                for line in log_file:
                    match_file_id = re.search(file_id_regex, line)
                    match_referrer = re.search(referrer_url, line)

                    if not match_file_id or not match_referrer or "403 AccessDenied" in line:
                        continue

                    aggregated_log.write(line)

            os.remove(f'{download_folder}/{filename}')


def aggregate_logs_in_period(date_range: pandas.DatetimeIndex, s3_bucket: str,
                             s3_path: str, regex: str, referrer_url: str):
    LOG_PATH = os.environ.get("AGGREGATED_LOG_PATH", None)
    shutil.rmtree(f'{LOG_PATH}{s3_bucket}', ignore_errors=True)
    today = pandas.Timestamp.today()

    for date in date_range:
        if date > today:
            print("No logs exist past today's date: ",
                  today.strftime("%b %d, %Y"))
            break

        folder_name = date.strftime("%Y/%m/%d")
        aggregate_logs_in_day(s3_bucket, s3_path, folder_name,
                              regex, referrer_url)
