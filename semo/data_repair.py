#!.venv/bin/python3

import utils, database as db
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(utils.get_log_file())
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(utils.get_log_format()))
logger.addHandler(file_handler)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(utils.get_log_format()))
logger.addHandler(stream_handler)


# lost fsid, inode, PATH
# lost fsid, INODE, path
# lost fsid, INODE, PATH
# lost FSID, inode, path
# lost FSID, inode, PATH
# lost FSID, INODE, path
# lost FSID, INODE, PATH

# inconsistent path
def fix_path_from_path(old_path : str, new_path : str):
    database = db.Database(utils.get_working_db())
    entry = database.get_file_entry_from_path(old_path)
    if entry is None:
        logger.error("didnt find entry by old path")
        return
    if len(entry) > 1:
        logger.error("more than one entry for old path")
        return
    entry = entry[0]
    database.set_file_path(fsid=entry[0], inode=entry[1], path=new_path)

def fix_path_from_fsid_inode(fsid : int, inode : int):
    # for item in watched dirs. check
    logger.info("have to rescan directory")
    return
    
def fix_inode_from_fsid_path(fsid : int, path : str):
    pass





def missing_fsid_INODE_path():
    pass

def missing_FSID_inode_path():
    pass

