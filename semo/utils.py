#! /usr/bin/env python3

"""Module to distribute necessary persistent information to other modules.

Contains the following functions:

    * home - returns path to semo data directory
    * dataset - loads and returns data from semo data file
    * get_working_db - returns currently active database path
    * set_working_db - changes currently active database path
    * get_test_db - returns database path used for tests
    * get_default_db - returns regular user database path (used to restate working database after testing)
    * get_fs_mountpoint - returns path to mounting directory
    * get_log_file - returns path to log file
    * get_log_format - returns format string for logs
    * get_watches - returns list of watch-tree root directories
    * set_watch - adds watch-tree to watchlist
    * mod_watch - modifies watch
    * sleep_watch - removes watch-tree from watchlist
    * get_fsid_and_inode - returns fsid and inode for given file
    * is_integer_string - returns if string can be converted to integer

Contains the following classes:

    * SemoException - wrapper around Exception to ensure relevant exceptions aren't accidentally handled
"""

import os,json

def home():
    """Gets and provides path to semo home directory.

    Returns
    -------
    str
        absolute path
    """

    #return os.path.expandvars('~/.semo')
    return "/home/mercury/.semo"
    #return os.path.expanduser('~') + '/.semo'

def dataset():
    """Reads and loads data from json file.

    Returns
    -------
    dict
        dict of semo data
    """

    with open(home() + '/data.json', 'r') as f:
        data = json.load(f)
    return data

def get_working_db() -> str:
    """Gets and provides path to current working database.

    Returns
    -------
    str
        absolute path
    """

    data = dataset()
    return data.get('working_db')

def set_working_db(db_path : str | None = None) -> None:
    """Sets working database to provided database path or default database path.

    Parameters
    ----------
    db_path : str | None, optional
        absolute path to database file, default is None
    """

    data = dataset()
    if not db_path:
        db_path = data['default_db']
    data['working_db'] = db_path
    with open(home() + '/data.json', 'w') as f:
        json.dump(data, f)
    return

def get_test_db() -> str:
    """Gets and provides path to testing database.

    Returns
    -------
    str
        absolute path
    """
    
    data = dataset()
    return data.get('test_db')

def get_default_db() -> str:
    """Gets and provides path to default database.

    Returns
    -------
    str
        absolute path
    """

    data = dataset()
    return data.get('default_db')

def get_fs_mount_point() -> str:
    """Gets and provides path to mounting directory.

    Returns
    -------
    str
        absolute path
    """

    data = dataset()
    return data.get('fs_mount_point')

def get_log_file() -> str:
    """Returns path to log file.

    Returns
    -------
    str
        absolute path
    """

    return home() + '/semo.log'

def get_log_format() -> str:
    """Returns log format string.

    Returns
    -------
    str
        log format string
    """

    return '%(name)s %(levelname)s (%(asctime)s) - %(message)s'

def get_watches() -> list[str]:
    """Gets and provides a list of paths to watched directory trees.

    Returns
    -------
    list[str]
        list of absolute paths to watch-tree root directories 
    """

    data = dataset()
    return data["watches"]
    return data.get('watches', [])

def set_watch(path) -> None:
    """Adds provided path to watchlist.

    Parameters
    -------
    path : str
        Absolute path to directory to add to watchlist
    """

    if not os.path.exists(path) or not os.path.isdir(path) or home() in path: raise SemoException("invalid directory path")
    data = dataset()
    data['watches'].append(path)
    with open(home() + '/data.json', 'w') as f:
        json.dump(data, f)

def mod_watch(old_path, new_path) -> None:
    """Modifies watchlist entry for the provided watch

    Parameters
    -------
    old_path : str
        Former path to directory (absolute)
    new_path : str
        Current path to directory (absolute)

    Raises
    ------
    SemoException
        If trying to modify a watch not in watchlist
    """

    if not os.path.exists(new_path) or not os.path.isdir(new_path): raise SemoException("invalid directory path")
    data = dataset()
    if old_path in data['watches']:
        data['watches'][data['watches'].index(old_path)] = new_path
        with open(home() + '/data.json', 'w') as f:
            json.dump(data, f)
        return
    raise SemoException("path not watched or not root of watch tree")

def sleep_watch(path) -> None:
    """Removes provided path from watchlist

    Parameters
    -------
    path : str
        Absolute path to directory to remove from watchlist
    """

    data = dataset()
    if path in data['watches']:
        data['watches'].remove(path)
    with open(home() + '/data.json', 'w') as f:
        json.dump(data, f)

def get_fsid_and_inode(filename : str) -> tuple[int, int]:
    """Gets filesystem ID and inode number for file at provided path

    Parameters
    -------
    path : str
        Absolute path

    Returns
    -------
    tuple[int, int]
        (fsid, inode) pair

    Raises
    ------
    SemoException
        If module os raises FileNotFoundError
    """
    try:
        return (os.statvfs(filename).f_fsid, os.stat(filename).st_ino)
    except FileNotFoundError:
        raise SemoException(f"File not found {filename}")
    
def is_integer_string(string) -> bool:
    """Decide if string is convertible to int

    Parameters
    -------
    string : str

    Returns
    -------
    bool
        True if string can be converted to int
    """
    try:
        _ = int(string)
        return True
    except (ValueError, TypeError):
        return False
class SemoException(Exception):
    """Functions as a wrapper around Exception to ensure relevant exceptions aren't accidentally handled"""
    pass
