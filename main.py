import os
import newrelic.agent

import argparse
import inspect

from load_env import load_env_file
from logger import create_log


if os.environ.get('NEW_RELIC_LICENSE_KEY', None):
    newrelic.agent.initialize(
        config_file='newrelic.ini',
        environment=os.environ.get('ENVIRONMENT', 'local')
    )


def main(args):
    logger = create_log(__name__)

    environment = args.environment
    process = args.process
    process_type = args.ingestType
    custom_file = args.inputFile
    start_date = args.startDate
    single_record = args.singleRecord
    limit = args.limit
    offset = args.offset
    options = args.options

    logger.info(f'Starting process {process} in {environment}')

    available_processes = register_processes()

    try:
        process_class = available_processes[process]
        
        process_instance = process_class(process_type, custom_file, start_date, single_record, limit, offset, options)
    except:
        logger.exception(f'Failed to initialize process {process} in {environment}')
        return

    if process in ('APIProcess', 'DevelopmentSetupProcess', 'MigrationProcess'):
        process_instance.runProcess()
    else:
        app = newrelic.agent.register_application(timeout=10.0)
        
        with newrelic.agent.BackgroundTask(app, name=process_instance):
            process_instance.runProcess()


def register_processes():
    import processes
    
    process_classes = inspect.getmembers(processes, inspect.isclass)
    
    return dict(process_classes)


def create_arg_parser():
    parser = argparse.ArgumentParser(description='Run DCDW Data Ingest Jobs')
    
    parser.add_argument('-p', '--process', required=True, help='The name of the process job to be run')
    parser.add_argument('-e', '--environment', required=True, help='Environment for deployment, sets env file to load')
    parser.add_argument('-i', '--ingestType', help='The interval to run the ingest over. Generally daily/complete/custom')
    parser.add_argument('-f', '--inputFile', help='Name of file to ingest. Ignored if -i custom is not set')
    parser.add_argument('-s', '--startDate', help='Start point for coverage period to query/process')
    parser.add_argument('-l', '--limit', help='Set overall limit for number of records imported in this process')
    parser.add_argument('-o', '--offset', help='Set start offset for current processed (for batched import process)')
    parser.add_argument('-r', '--singleRecord', help='Single record ID for ingesting an individual record')
    parser.add_argument('options', nargs='*', help='Additional arguments')

    return parser


if __name__ == '__main__':
    parser = create_arg_parser()
    args = parser.parse_args()

    load_env_file(args.environment, './config/{}.yaml')
    os.environ['ENVIRONMENT'] = args.environment

    main(args)
