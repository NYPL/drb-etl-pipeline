import sys

from analytics.upress_reporting.reports.models.downloads import DownloadsReport
from datetime import datetime
from logger import createLog
from main import loadEnvFile


def main():
    logger = createLog("Generating Counter 5 reports...")
    loadEnvFile('sample-compose', fileString='config/example.yaml')

    downloads_report = None

    if (len(sys.argv) <= 1):
        # TODO: should this warning be printed or logged?
        print(
            f"No reporting period passed in. Generating report for Jan {datetime.now().year}!")
    downloads_report = DownloadsReport("UofM") if (
        len(sys.argv) <= 1) else DownloadsReport("UofM", sys.argv[1])
    downloads_report.build_report()


if __name__ == '__main__':
    main()
