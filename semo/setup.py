#! /usr/bin/env python3

"""Data file constructor

Script that creates the required log and json file in the program's home directory and fills in the neccessary starting information.

This file is run as a script and contains the functions:
    * main - main function of the script

"""

import os, json

def main(*args):
    """Saves starting information to a json file."""
    
    homepath = args[0]
    dbpath = homepath + args[1]
    #watchpath = args[2]
    
    with open(homepath + "/semo.log", 'w') as f:
        pass
    with open(homepath + "/data.json", 'w') as f:
        data = {
        'working_db' : os.path.abspath(dbpath),
        'test_db' : f'{homepath}/tests/testDB.db',
        'default_db' : os.path.abspath(dbpath),
        'fs_mount_point' : f'{homepath}/mnt',
        'watches' : []
        }
        json.dump(data, f)

if __name__ == "__main__":
    main()
