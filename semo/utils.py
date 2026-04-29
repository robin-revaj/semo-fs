#!.venv/bin/python3

import configparser

config = configparser.ConfigParser()
config.read('config.ini')

def get_working_db() -> str:
    return config.get('BASIC', 'working_db')

def set_working_db(db_path : str | None = None) -> None:
    if db_path is None:
        db_path = get_BASIC_db()
    config.set('BASIC','working_db', db_path)
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

def get_test_db() -> str:
    return config.get('BASIC', 'test_db')

def get_BASIC_db() -> str:
    return config.get('BASIC', 'BASIC_db')

def get_fs_mount_point() -> str:
    return config.get('BASIC', 'fs_mount_point')

def get_log_file() -> str:
    return 'semo.log'

def get_log_format() -> str:
    return '%(name)s %(levelname)s (%(asctime)s) - %(message)s'

def watch_index() -> str:
    return config.get('BASIC', 'watch_index')
def get_watches() -> list:
    return [x[1] for x in config.items('WATCHES')]
def set_watch(path):
    config.set('WATCHES', 'watch' + watch_index(), path)
    config.set('BASIC', 'watch_index', str(int(watch_index()) + 1))
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
def mod_watch(path):
    config.set('WATCHES', 'watch' + watch_index(), path)
def sleep_watch(path):
    i = get_watches().index(path)
    config.remove_option('WATCHES', 'watch' + watch_index())
class SemoException(Exception):
    pass