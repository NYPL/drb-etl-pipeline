import argparse
import inspect
import os
import sys
import yaml

def main(args):
    process = args.process
    procType = args.ingestType
    customFile = args.inputFile
    startDate = args.startDate
    limit = args.limit
    offset = args.offset

    availableProcesses = registerProcesses()

    procClass = availableProcesses[process]
    processInstance = procClass(procType, customFile, startDate, limit, offset)
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