import os
import yaml


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
