import sys

from analytics.upress_reporting.counter_5_controller import Counter5Controller
from datetime import datetime
from logger import createLog
from main import load_env_file


def main():
    logger = createLog("runner")
    load_env_file('local-compose', file_string='config/local-compose.yaml')

    if (len(sys.argv) <= 1):
        print(
            f"No reporting period passed in. Generating report for Jan {datetime.now().year}!")

    counter_5_controller = Counter5Controller(None) if (
        len(sys.argv) <= 1) else Counter5Controller(sys.argv[1])
    counter_5_controller.create_reports()


if __name__ == '__main__':
    main()
