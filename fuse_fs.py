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

class semoFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)
        self.mnt = utils.get_fs_mount_point()
        self.root = "/"
        self.database = backend.db.Database(utils.get_working_db())
        self.validator = backend.v.Validator(self.database)

    def readdir(self, path, offset):
        entries = {".", ".."}
        if path == "/":
            entries.update(backend.query_LIST_ROOTS())
        else:
            tagname = path.strip("/").split("/")[-1]
            entries.update(backend.query_LIST_DIRECT_SUBTAGS(tagname))
            entries.update(backend.query_LIST_FILES_FOR_TAG(tagname, limit_to_direct=True))

        for e in entries:
            yield fuse.Direntry(e)

    def getattr(self, path):
        st = fuse.Stat()
        if path == "/":
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            return st
        
        path_parts = path.strip("/").split("/")


        if self.validator.tag_exists(path_parts[-1]):
            st.st_mode = stat.S_IFDIR | 0o755
            st.st_nlink = 2
            return st

        if len(path_parts) < 2:
            return errno.ENOENT
        
        parent, child = path_parts
        
        if self.validator.tag_exists(parent):
            child_files = backend.query_LIST_FILES_FOR_TAG(parent, limit_to_direct=True)
            for file_system, inode, unconfirmed_path in child_files:
                if unconfirmed_path.endswith(child):
                    st.st_mode = stat.S_IFREG | 0o644
                    st.st_nlink = 1
                    st.st_size = os.path.getsize(unconfirmed_path)
                    st.st_ino = inode
                    return st

        return errno.ENOENT
    
    def read(self, path, size, offset):
        with open(self.root + path, "rb") as f:
            f.seek(offset)
            return f.read(size)
    
def main():
    fuse.fuse_python_api = (0, 2)
    fs = semoFS(version="%prog " + "0", usage=fuse.Fuse.fusage)
    fs.parse(errex=1)
    fs.main()

if __name__ == "__main__":
    main()