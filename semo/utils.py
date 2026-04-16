#!.venv/bin/python3

import configparser

config = configparser.ConfigParser()
config.read('config.ini')

def get_working_db() -> str:
    return config['DEFAULT']['working_db']

def set_working_db(db_path : str) -> None:
    config['DEFAULT']['working_db'] = db_path
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def get_test_db() -> str:
    return config['DEFAULT']['test_db']

def get_default_db() -> str:
    return config['DEFAULT']['default_db']

def get_fs_mount_point() -> str:
    return config['DEFAULT']['fs_mount_point']

def get_log_file() -> str:
    return 'semo.log'

def get_log_format() -> str:
    return '%(name)s %(levelname)s (%(asctime)s) - %(message)s'