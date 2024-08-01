import sys

from analytics.upress_reporting.models.reports.downloads import DownloadsReport
from datetime import datetime
from logger import createLog
from main import loadEnvFile


def main():
    logger = createLog("Generating Counter 5 reports...")
    loadEnvFile('local-compose', fileString='config/local-compose.yaml')

    downloads_report = None

    if (len(sys.argv) <= 1):
        print(
            f"No reporting period passed in. Generating report for Jan {datetime.now().year}!")
    downloads_report = DownloadsReport("UofM") if (
        len(sys.argv) <= 1) else DownloadsReport("UofM", sys.argv[1])
    downloads_report.build_report()


if __name__ == '__main__':
    main()
