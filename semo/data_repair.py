#!.venv/bin/python3

#import logging
import os 
import utils, validator as v, database as db
from utils import SemoException



# lost fsid, inode, PATH
# lost fsid, INODE, path
# lost fsid, INODE, PATH
# lost FSID, inode, path
# lost FSID, inode, PATH
# lost FSID, INODE, path
# lost FSID, INODE, PATH

#ic.IN_DELETE_SELF | ic.IN_MOVE_SELF | ic.IN_UNMOUNT | ic.IN_DELETE | ic.IN_MOVED_FROM | ic.IN_MOVED_TO

def in_umount(event_types, path):
    database = db.Database(utils.get_working_db())
    entries = database.get_files_by_path_prefix(path)
    if entries is not None and len(entries) > 0:
        fsid = entries[0][0]
        database.set_fs_sleep(fsid)
        
def in_delete(event_types, path):
    database = db.Database(utils.get_working_db())
    f_entry = database.get_file_by_path(path)
    if f_entry is not None and len(f_entry) > 0:
        database.delete_file(f_entry[0], f_entry[1])

def in_moved_outside_watched_region(event_types, path):
    handle_file_location_loss(path)

def in_moved_within_watched_region(event_types, former_path, new_path):
    handle_file_location_change(former_path, new_path)

def handle_file_location_change(former_path : str, new_path : str):
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    fsid, inode = utils.get_fsid_and_inode(new_path)
    database.set_file_path(fsid, inode, new_path)

    if os.path.isdir(new_path):
        entries = database.get_files_by_path_prefix(former_path + "/")
        if len(entries) > 0:
            for entry_fsid, entry_inode, entry_path, entry_id in entries:
                new_entry_path = entry_path.replace(former_path, new_path, 1)
                database.set_file_path(entry_fsid, entry_inode, path=new_entry_path)
                fsid, inode = utils.get_fsid_and_inode(new_entry_path)
                database.set_file_fsid_inode(fsid, inode, new_entry_path)

def handle_file_location_loss(former_path : str):
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    entry = database.get_file_by_path(former_path)
    if entry is not None:
        fsid, inode, _, _ = entry
        database.delete_file(fsid, inode)
        #os.system("notify-send 'file moved outside of watched region' '{}'".format(former_path))
    entries = database.get_files_by_path_prefix(former_path + "/")
    if len(entries) > 0:
        for fsid, inode, path, entry_id in entries:
            database.delete_file(fsid, inode)

def recover_fsid_inode_from_abspath(path : str, force_delete : bool = True) -> list:
    database = db.Database(utils.get_working_db())
    file_records = database.get_files_by_path_prefix(path)

    recovered = []

    if file_records is None or len(file_records) == 0:
        return []
    for form_fsid, form_inode, path, entry_id in file_records:
        try:
            fsid, inode = utils.get_fsid_and_inode(path)
            if fsid != form_fsid or inode != form_inode:
                database.set_file_fsid_inode(fsid, inode, path)
            recovered.append(path)
        except:
            if force_delete: database.delete_file(form_fsid, form_inode)
    return recovered

def recover_path_by_inode(path : str, force_delete : bool = True):
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

def recover_path_inode_by_mountpath(mountpath : str, force_delete : bool = True) -> list:
    database = db.Database(utils.get_working_db())
    
    recovered = []

    for contents in os.walk(mountpath):
        prefix, dirs, files = contents
        for item in dirs + files:
            fsid, inode = utils.get_fsid_and_inode(os.path.join(prefix, item))
            local_path = os.path.join(prefix.replace(mountpath, "", 1), item)
            entries = database.get_files_by_path_suffix(local_path)
            if entries is not None and len(entries) > 0:
                for entry_fsid, entry_inode, entry_path, entry_id in entries:
                    if entry_fsid == fsid:
                        database.set_file_path(fsid, entry_inode, os.path.join(prefix, item))
                        database.set_file_fsid_inode(fsid, inode, os.path.join(prefix, item))
                        recovered.append(os.path.join(prefix, item))
    return recovered

def partial_recover_path_inode_by_mountpath(mountpath : str, force_delete : bool = True) -> list:
    database = db.Database(utils.get_working_db())
    
    recovered = []
    indistinct = []

    for contents in os.walk(mountpath):
        prefix, dirs, files = contents
        for item in dirs + files:
            fsid, inode = utils.get_fsid_and_inode(os.path.join(prefix, item))
            local_path = os.path.join(prefix.replace(mountpath, "", 1), item)
            entries = database.get_files_by_path_suffix(local_path)
            if entries is not None and len(entries) > 0:
                if len(entries) == 1:
                    for entry_fsid, entry_inode, entry_path, entry_id in entries:
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
    