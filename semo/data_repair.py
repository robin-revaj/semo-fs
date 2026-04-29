#!.venv/bin/python3

import logging
import os 
from . import utils, validator as v, database as db, os_calls, backend
import inotify.constants



# lost fsid, inode, PATH
# lost fsid, INODE, path
# lost fsid, INODE, PATH
# lost FSID, inode, path
# lost FSID, inode, PATH
# lost FSID, INODE, path
# lost FSID, INODE, PATH

#ic.IN_DELETE_SELF | ic.IN_MOVE_SELF | ic.IN_UNMOUNT | ic.IN_DELETE | ic.IN_MOVED_FROM | ic.IN_MOVED_TO

def semo_concerned(path, filename) -> bool:
    try:
        fsid, inode = os_calls.retrieve_inode_from_path(os.path.join(path, filename))
    except:
        return False
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    return validator.file_exists(fsid, inode)

def in_umount(e, path, filename):
    database = db.Database(utils.get_working_db())
    entries = database.get_files_by_path_prefix(os.path.join(path, filename))
    if entries is not None:
        fsid = entries[0][0]
        database.set_fs_sleep(fsid)
        
def in_delete(e, path, filename):
    former_path = os.path.join(path, filename)
    database = db.Database(utils.get_working_db())
    f_entry = database.get_file_by_path(former_path)
    if f_entry is not None:
        database.delete_file(f_entry[0], f_entry[1])

def in_moved_outside_watched_region(e, path, filename):
    former_path = os.path.join(path, filename)
    os.system("notify-send 'file moved outside of watched region' '{}'".format(former_path))
    handle_file_location_loss(former_path)

def in_moved_within_watched_region(e, path, filename):
    handle_file_location_change(os.path.join(path, filename))

def handle_file_location_change(new_path : str):
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    fsid, inode = os_calls.retrieve_inode_from_path(new_path)
    if validator.file_exists(fsid, inode):
        database.set_file_path(fsid=fsid, inode=inode, path=new_path)

def handle_file_location_loss(former_path : str):
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    entries = database.get_files_by_path_prefix(former_path)
    if entries is not None:
        for fsid, inode, path, entry_id in entries:
            database.delete_file(fsid, inode)

def handle_fsid_and_inode_loss():
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    file_records = database.get_files_with_paths()
    for form_fsid, form_inode, path, entry_id in file_records:
        try:
            fsid, inode = os_calls.retrieve_inode_from_path(path)
            if fsid != form_fsid or inode != form_inode:
                database.set_file_fsid_inode(fsid, inode, path)
        except:
            database.delete_file(form_fsid, form_inode)

def export_data_to_xattr(filepath):
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    fsid, inode = os_calls.retrieve_inode_from_path(filepath)
    if validator.file_exists(fsid, inode):
        semo_data = database._direct_rels_for_file(fsid, inode)
        data_string = " ".join(f"{k}:{v}" for k, v in semo_data.items())
        os.setxattr(filepath, "user.semo", data_string.encode())

def import_data_from_xattr(filepath):
    data_string = os.getxattr(filepath, "user.semo").decode()
    semo_data = dict(item.split(":") for item in data_string.split())
    for k, v in semo_data.items():
        backend.connect_tag(filepath, k, v)

# def in_follow_move(path, filename) -> bool:
#     try:
#         fsid, inode = os_calls.retrieve_inode_from_path(path)
#     except:
#         return False
#     database = db.Database(utils.get_working_db())
#     validator = v.Validator(database)
#     return validator.file_exists(fsid, inode)






# inconsistent path
# def fix_path_from_path(old_path : str, new_path : str):
#     database = db.Database(utils.get_working_db())
#     validator = v.Validator(database)

#     fsid, inode = os_calls.retrieve_inode_from_path(new_path)
#     if validator.file_exists(fsid, inode):
#         database.set_file_path(fsid=fsid, inode=inode, path=new_path)
#     return (old_path, new_path)

# def fix_path_from_fsid_inode(fsid : int, inode : int):
#     # for item in watched dirs. check
#     logger.info("have to rescan directory")
#     return
    
# def fix_inode_from_fsid_path(fsid : int, path : str):
#     pass





def missing_fsid_INODE_path():
    pass

def missing_FSID_inode_path():
    pass

