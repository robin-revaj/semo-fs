#!/usr/bin/env python3

import fuse
import os

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

class Filesystem(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)
        self.src_dir = "."

    def readdir(self, path, offset):
        for f in os.listdir(self.src_dir + path):
            yield fuse.Direntry(f)

    def getattr(self, path):
        st = semoStat()

        real_st = os.stat(path)

        st.st_mode = real_st.st_mode
        st.st_ino = real_st.st_ino
        st.st_dev = real_st.st_dev
        st.st_nlink = real_st.st_nlink
        st.st_uid = real_st.st_uid
        st.st_gid = real_st.st_gid
        st.st_size = real_st.st_size
        st.st_atime = real_st.st_atime
        st.st_mtime = real_st.st_mtime
        st.st_ctime = real_st.st_ctime
        st.tags = ["a", "b", "c"] # TODO query tags for file from backend

        return st
    
def main():
    fuse.fuse_python_api = (0, 2)
    fs = Filesystem(version="%prog " + "0", usage=fuse.Fuse.fusage)
    fs.parse(errex=1)
    fs.main()

if __name__ == "__main__":
    main()