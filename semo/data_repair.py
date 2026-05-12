#! /usr/bin/env python3

"""Contains functions to respond and adapt to file system changes

Both handles observed live changes and reconstructs database data after changes occured unobserved.

File should be imported as a module and contains the following functions:

    * in_umount(path) - responds to watcher registering umount event
    * in_delete(path) - responds to watcher registering delete event
    * in_moved_outside_watched_region(path) - responds to watcher registering moved_from but not moved_to event
    * in_moved_within_watched_region(path) - responds to watcher registering moved_from and moved_to event
    * recover_fsid_inode_from_abspath(path, force_delete) - repairs inconstistent database entries relying on path accuracy
    * recover_path_by_inode(path) - repairs inconsisent database entries relying on (fsid, inode) accuracy
    * recover_path_inode_by_mountpath(mountpath) - repairs inconsistent database entries relying on paths relative to mountpoint
    * partial_recover_path_inode_by_mountpath(mountpath, force_delete) - attempts to repair inconsistent database entries relying on paths relative to mountpoint but not fsid
"""

import os 
import utils, validator as v, database as db
from utils import SemoException


def in_umount(path : str):
    """Responds to watcher registering umount event, sets filesystem entry as asleep

    Parameters
    ----------
    path : str
    """

    database = db.Database(utils.get_working_db())
    entries = database.get_files_by_path_prefix(path)
    if entries:
        fsid = entries[0][0]
        database.set_fs_sleep(fsid)
        
def in_delete(path : str):
    """Responds to watcher registering delete event, deletes if exists entry for given path

    Parameters
    ----------
    path : str
    """

    database = db.Database(utils.get_working_db())
    f_entry = database.get_file_by_path(path)
    if f_entry:
        database.delete_file(f_entry[0], f_entry[1])

def in_moved_within_watched_region(former_path : str, new_path : str):
    """Handles file location change from former path to new path.

    Updates path for given entry and if entry is a directory updates entries for files in it

    Parameters
    ----------
    former_path : str
    new_path : str
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    fsid, inode = utils.get_fsid_and_inode(new_path)
    database.set_file_path(fsid, inode, new_path)

    if os.path.isdir(new_path) and former_path:
        entries = database.get_files_by_path_prefix(former_path + "/")
        for entry_fsid, entry_inode, entry_path, entry_id in entries:
            new_entry_path = entry_path.replace(former_path, new_path, 1)
            database.set_file_path(entry_fsid, entry_inode, new_entry_path)
            fsid, inode = utils.get_fsid_and_inode(new_entry_path)
            database.set_file_fsid_inode(fsid, inode, new_entry_path)     

def in_moved_outside_watched_region(former_path : str):
    """Handles file location change from former path to unknown. Deletes outdated entries.

    Deletes given entry and if entry is a directory deletes entries for files in it

    Parameters
    ----------
    former_path : str
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    entry = database.get_file_by_path(former_path)
    if entry is not None:
        fsid, inode, _, _ = entry
        database.delete_file(fsid, inode)
    entries = database.get_files_by_path_prefix(former_path + "/")
    for fsid, inode, _, _ in entries:
        database.delete_file(fsid, inode)

def recover_fsid_inode_from_abspath(path : str, force_delete : bool = True) -> list[str]:
    """Repairs inconstistent database entries relying on path accuracy
    
    Parameters
    ----------
    path : str
    force_delete : bool, optional
        If set, deletes entries that couldn't be updated. Default is True

    Returns
    -------
    list[str]
        Paths for which entries were recovered
    """
    
    database = db.Database(utils.get_working_db())
    file_records = database.get_files_by_path_prefix(path)

    recovered = []

    # if file_records is None or len(file_records) == 0:
    #     return []
    for form_fsid, form_inode, path, entry_id in file_records:
        try:
            fsid, inode = utils.get_fsid_and_inode(path)
            if fsid != form_fsid or inode != form_inode:
                database.set_file_fsid_inode(fsid, inode, path)
            recovered.append(path)
        except:
            if force_delete: database.delete_file(form_fsid, form_inode)
    return recovered

def recover_path_by_inode(path : str) -> list[str]:
    """Repairs inconstistent database entries relying on (fsid, inode) accuracy
    
    Parameters
    ----------
    path : str

    Returns
    -------
    list[str]
        Paths for which entries were recovered
    """
    
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    
    recovered = []

    for contents in os.walk(path):
        prefix, dirs, files = contents
        for item in dirs + files:
            fsid, inode = utils.get_fsid_and_inode(os.path.join(prefix, item))
            if validator.file_exists(fsid, inode):
                database.set_file_path(fsid, inode, os.path.join(prefix, item))
                recovered.append(os.path.join(prefix, item))
    return recovered

def recover_path_inode_by_mountpath(mountpath : str) -> list[str]:
    """Repairs inconsistent database entries relying on paths relative to mountpoint and fsid
    
    Parameters
    ----------
    path : str

    Returns
    -------
    list[str]
        Paths for which entries were recovered
    """
    
    database = db.Database(utils.get_working_db())
    
    recovered = []

    for contents in os.walk(mountpath):
        prefix, dirs, files = contents
        for item in dirs + files:
            fsid, inode = utils.get_fsid_and_inode(os.path.join(prefix, item))
            local_path = os.path.join(prefix.replace(mountpath, "", 1), item)
            entries = database.get_files_by_path_suffix(local_path)
            #if entries is not None and len(entries) > 0:
            for entry_fsid, entry_inode, entry_path, entry_id in entries:
                if entry_fsid == fsid:
                    database.set_file_path(fsid, entry_inode, os.path.join(prefix, item))
                    database.set_file_fsid_inode(fsid, inode, os.path.join(prefix, item))
                    recovered.append(os.path.join(prefix, item))
    return recovered

def partial_recover_path_inode_by_mountpath(mountpath : str, force_delete : bool = True) -> list:
    """Attempts to repair inconsistent database entries relying on paths relative to mountpoint but not fsid
    
    Parameters
    ----------
    path : str
    force_delete : bool, optional
        If set, deletes entries that couldn't be updated. Default is True

    Returns
    -------
    list[list[str]]
        On index 0 - paths for which entries were recovered, on index 1 - paths which couldn't be reliably recovered
    """
    database = db.Database(utils.get_working_db())
    
    recovered = []
    indistinct = []

    for contents in os.walk(mountpath):
        prefix, dirs, files = contents
        for item in dirs + files:
            fsid, inode = utils.get_fsid_and_inode(os.path.join(prefix, item))
            local_path = os.path.join(prefix.replace(mountpath, "", 1), item)
            entries = database.get_files_by_path_suffix(local_path)
            #if entries is not None and len(entries) > 0:
            if len(entries) == 1:
                entry_fsid, entry_inode, entry_path, entry_id = entries[0]
                database.set_file_path(entry_fsid, entry_inode, os.path.join(prefix, item))
                database.set_file_fsid_inode(fsid, inode, os.path.join(prefix, item))
                recovered.append(os.path.join(prefix, item))
            else:
                if force_delete: 
                    for entry_fsid, entry_inode, entry_path, entry_id in entries:
                        database.delete_file(entry_fsid, entry_inode)
                else:
                    indistinct.append((p for _, _, p, _ in entries))

    return [recovered, indistinct]
    