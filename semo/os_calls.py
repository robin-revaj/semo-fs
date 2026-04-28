import os
import logging

from . import settings 
from semo.utils import SemoException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

def retrieve_inode_from_path(filename : str):
    try:
        return (os.statvfs(filename).f_fsid, os.stat(filename).st_ino)
    except FileNotFoundError:
        logger.exception(f"Error retrieving fsid, inode for file '{filename}'")
        raise SemoException(f"File not found {filename}")

    