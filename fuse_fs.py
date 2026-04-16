#!/usr/bin/env python3

import errno

import fuse, os, stat
from semo import backend, utils, validator

class semoStat(fuse.Stat):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # HELP
        self.st_mode = 0
        self.st_nlink = 0
        self.st_atime = 0.0
        self.st_mtime = 0.0 
        self.st_ctime = 0.0 

        self.tags : list[str] = []
import time, sys, signal
class semoFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)
        self.database = backend.db.Database(utils.get_working_db())
        self.validator = backend.v.Validator(self.database)

    def readdir(self, path, offset):
        entries = [".", ".."]
        tags = []
        files = []

        if path == "/":
            tags.extend(backend.get_roots())
        else:
            segmented_path = path.strip("/").split("/")
            current_item = segmented_path[-1]
            tags.extend(backend.get_subtags_DIRECT(current_item))
            try:
                filepaths = backend.get_files_for_tag_DIRECT(tag_name=current_item)
                filenames = [os.path.basename(f) for f in filepaths]
                files.extend(filenames)
            except Exception as e:
                files.extend((str(e),))

        entries.extend(tags)
        entries.extend(files)
        for e in entries:
            yield fuse.Direntry(e)

    def getattr(self, path):
        st = fuse.Stat()

        if path == "/":
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = 2
            return st
        
        segmented_path = path.strip("/").split("/")
        current_item = segmented_path[-1]
        for tagname in backend.get_all_tags():
            if current_item == tagname:
                st.st_mode = stat.S_IFDIR | 0o555
                st.st_nlink = 2
                return st
        
        if len(segmented_path) > 1:
            parent_tag = segmented_path[-2]
            for fsid, inode, filepath in backend.get_files_for_tag_DIRECT(parent_tag, long_format=True):
                filename = os.path.basename(filepath)
                if current_item == filename:
                    real_st = os.stat(filepath)
                    st.st_mode = stat.S_IFLNK | 0o555
                    st.st_nlink = real_st.st_nlink
                    st.st_size = real_st.st_size

                    return st
                

        return errno.ENOENT

    def readlink(self, path):
        segmented_path = path.strip("/").split("/")
        current_item = segmented_path[-1]
        if len(segmented_path) > 1:
            parent_tag = segmented_path[-2]
            for fsid, inode, filepath in backend.get_files_for_tag_DIRECT(parent_tag, long_format=True):
                filename = os.path.basename(filepath)
                if current_item == filename:
                    return filepath
        return ""
                    
def main():
    fuse.fuse_python_api = (0, 2)
    fs = semoFS(version="%prog " + "0", usage=fuse.Fuse.fusage)
    fs.parse(errex=1)
    fs.main()

if __name__ == "__main__":
    main()