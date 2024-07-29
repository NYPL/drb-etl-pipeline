from datetime import datetime
from analytics.upress_reporting.reports.models.downloads import DownloadsReport
from logger import createLog

import sys

def main():
    logger = createLog("Generating Counter 5 reports...")

    if (len(sys.argv) >= 1):
        print(f"No reporting period passed in. Generating report for Jan {datetime.now().year}")
    
    downloads_report = DownloadsReport("UofM", sys.argv[1])
    downloads_report.build_report()

if __name__ == '__main__':
    main()