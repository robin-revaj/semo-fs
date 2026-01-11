import os

def retrieve_inode_from_path(filename : str):
    try:
        return (0, os.stat(filename).st_ino)
    except Exception as e:
        raise e