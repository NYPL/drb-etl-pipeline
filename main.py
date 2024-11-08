import os
import newrelic.agent

import argparse
import inspect

from load_env import load_env_file
from logger import createLog

#NEW_RELIC_LICENSE_KEY = Put license key here
#ENVIRONMENT = Put environment here

if os.environ.get('NEW_RELIC_LICENSE_KEY', None):
    newrelic.agent.initialize(
        config_file='newrelic.ini',
        environment=os.environ.get('ENVIRONMENT', 'local')
        )

def main(args):
    logger = createLog(__name__)

    environment = args.environment
    process = args.process
    procType = args.ingestType
    customFile = args.inputFile
    startDate = args.startDate
    singleRecord = args.singleRecord
    limit = args.limit
    offset = args.offset
    options = args.options

    logger.info('Starting process {} in {}'.format(process, environment))
    logger.debug('Process Args Type: {}, Limit: {}, Offset: {}, Date: {}, File: {}, Record: {}'.format(
        procType, limit, offset, startDate, customFile, singleRecord
    ))

    availableProcesses = registerProcesses()

    try:
        procClass = availableProcesses[process]
        processInstance = procClass(
            procType, customFile, startDate, singleRecord, limit, offset, options
        )
    except:
        logger.exception(f'Failed to initialize process {process} in {environment}')
        return

    if process in (
        "APIProcess", # Covered by newrelic's automatic Flask integration
        "DevelopmentSetupProcess",
        "MigrationProcess",
    ):
        processInstance.runProcess()
    else:
        app = newrelic.agent.register_application(timeout=10.0)
        with newrelic.agent.BackgroundTask(app, name=process):
            logger.info(f'Running process {process} in {environment}')
            processInstance.runProcess()


def registerProcesses():
    import processes
    procs = inspect.getmembers(processes, inspect.isclass)
    return dict(procs)


def createArgParser():
    parser = argparse.ArgumentParser(description='Run DCDW Data Ingest Jobs')
    parser.add_argument('-p', '--process', required=True,
                        help='The name of the process job to be run')
    parser.add_argument('-e', '--environment', required=True,
                        help='Environment for deployment, sets env file to load')
    parser.add_argument('-i', '--ingestType',
                        help='The interval to run the ingest over. Generally daily/complete/custom')
    parser.add_argument('-f', '--inputFile',
                        help='Name of file to ingest. Ignored if -i custom is not set')
    parser.add_argument('-s', '--startDate',
                        help='Start point for coverage period to query/process')
    parser.add_argument('-l', '--limit',
                        help='Set overall limit for number of records imported in this process')
    parser.add_argument('-o', '--offset',
                        help='Set start offset for current processed (for batched import process)')
    parser.add_argument('-r', '--singleRecord',
                        help='Single record ID for ingesting an individual record')
    parser.add_argument('options', nargs='*', help='Additional arguments')

    return parser


if __name__ == '__main__':
    parser = createArgParser()
    args = parser.parse_args()

    load_env_file(args.environment, './config/{}.yaml')
    os.environ['ENVIRONMENT'] = args.environment

    main(args)
