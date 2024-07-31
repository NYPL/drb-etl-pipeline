import os
import yaml


def load_env_file(run_type: str, file_string: str | None=None) -> None:
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
    env_dict = None

    if file_string:
        open_file = file_string.format(run_type)
    else:
        open_file = 'local.yaml'

    try:
        with open(open_file) as env_stream:
            try:
                env_dict = yaml.full_load(env_stream)
            except yaml.YAMLError as err:
                print(f'{open_file} Invalid! Please review')
                raise err

    except FileNotFoundError as err:
        print('Missing config YAML file! Check directory')
        raise err

    if env_dict:
        for key, value in env_dict.items():
            os.environ[key] = value
