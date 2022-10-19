import inspect
import sys
from main import loadEnvFile

loadEnvFile('local-qa', fileString='config/{}.yaml')

import scripts


def registerScripts():
    """
    Import any functions that have been defined in the scripts/ directory and
    have been added to the init file there.
    """
    scriptFuncs = inspect.getmembers(scripts, inspect.isfunction)
    return dict(scriptFuncs)


def loadScript(scriptName):
    """
    This takes the loaded script object and returns the function object for the 
    supplied key. If that script is not present an error is raised
    """
    scriptFuncs = registerScripts()

    try:
        return scriptFuncs[scriptName]
    except KeyError as e:
        print('Provided function name not recognized!')
        raise e


def fetchNameFromCLI():
    """Loads the name of the desired script from a positional CLI argument"""
    try:
        return sys.argv[1]
    except IndexError as e:
        print('Name of script to run required!')
        raise e


if __name__ == '__main__':
    # Get name of desired script from CLI,
    # this should be the only argument passed in
    scriptName = fetchNameFromCLI()

    # Load the appropriate script from the scripts/ directory
    currentScript = loadScript(scriptName)

    # Run the script
    currentScript()

    # TODO
    # Allow a user to define in what environment their script should be run
