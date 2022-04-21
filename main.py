import newrelic.agent
import os

#NEW_RELIC_LICENSE_KEY = Put license key here
#ENVIRONMENT = Put environment here

if os.environ.get('NEW_RELIC_LICENSE_KEY', None):
    newrelic.agent.initialize(
        config_file='newrelic.ini',
        environment=os.environ.get('ENVIRONMENT', 'local')
        )

import argparse
import inspect
import yaml

from logger import createLog


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

    logger.info('Staring Process {} in {}'.format(process, environment))
    logger.debug('Process Args Type: {}, Limit: {}, Offset: {}, Date: {}, File: {}, Record: {}'.format(
        procType, limit, offset, startDate, customFile, singleRecord
    ))

    availableProcesses = registerProcesses()

    procClass = availableProcesses[process]
    processInstance = procClass(
        procType, customFile, startDate, singleRecord, limit, offset, options
    )
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
                        help='Single record ID for ingesting an individual record (only applicable for DOAB)')
    parser.add_argument('options', nargs='*', help='Additional arguments')
    
    return parser


def loadEnvFile(runType, fileString=None):
    """Loads configuration details from a specific yaml file.
    Arguments:
        runType {string} -- The environment to load configuration details for.
        fileString {string} -- The file string format indicating where to load
        the configuration file from.
    Raises:
        YAMLError: Indicates malformed yaml markup in the configuration file
    Returns:
        dict -- A dictionary containing the configuration details parsed from
        the specificied yaml file.
    """
    envDict = None

    if fileString:
        openFile = fileString.format(runType)
    else:
        openFile = 'local.yaml'

    try:
        with open(openFile) as envStream:
            try:
                envDict = yaml.full_load(envStream)
            except yaml.YAMLError as err:
                print('{} Invalid! Please review'.format(openFile))
                raise err

    except FileNotFoundError as err:
        print('Missing config YAML file! Check directory')
        raise err

    if envDict:
        for key, value in envDict.items():
            os.environ[key] = value
    

if __name__ == '__main__':
    parser = createArgParser()
    args = parser.parse_args() 

    loadEnvFile(args.environment, './config/{}.yaml')
    os.environ['ENVIRONMENT'] = args.environment

    main(args)
