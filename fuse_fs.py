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

class semoDirentry(fuse.Direntry):
    def __init__(self, name, real_path, **kw):
        fuse.Direntry.__init__(self, name, **kw)
        self.real_path = real_path

import time, sys, signal
class semoFS(fuse.Fuse):
    def __init__(self, *args, **kwargs):
        fuse.Fuse.__init__(self, *args, **kwargs)
        self.database = backend.db.Database(utils.get_working_db())
        self.validator = backend.v.Validator(self.database)
    
    def disassemble_local_name(self, local_name) -> tuple[str, int]:
        try:
            filename, entry_id = local_name[:-1].rsplit('(', 1)
            return (filename, int(entry_id))
        except ValueError as e:
            return ("", 0)


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
                filedata = backend.get_files_for_tag_DIRECT(tag_name=current_item, long_format=True)
                filenames = []
                for _, _, filepath, database_id in filedata:
                    local_name = os.path.basename(filepath) + "(" + str(database_id) + ")"
                    filenames.append(local_name)
                # filepaths = [f[2] for f in filedata]
                # prefix = os.path.commonpath(filepaths)
                # filenames = [f[len(prefix):].replace("/", ">") for f in filepaths]
                # filenames = [os.path.basename(f) for f in filepaths]
                # filenames = []
                # for fsid, inode, filepath in filedata:
                #     filenames.append( os.path.basename(filepath) + f"({inode})" )
                # for fsid, inode, filepath in filedata:

                # filenames = [f[2].replace("/", "\\") for f in filedata]
                # if len(set(filenames)) < len(filenames):
                #     for i in range(len(filenames)):
                #         filenames[i] = f"({filepaths[i][1]})" + filenames[i]
                
                files.extend(filenames)
            except Exception as e:
                files.extend((str(e),))

        entries.extend(tags)
        entries.extend(files)
        for e in entries:
            yield semoDirentry(e, "")
        return offset

    def getattr(self, path):
        st = fuse.Stat()

        if path == "/":
            st.st_mode = stat.S_IFDIR | 0o555
            st.st_nlink = 2
            return st
        
        head, tail = os.path.split(path)
        segmented_path = path.strip("/").split("/")
        current_item = segmented_path[-1]
        for tagname in backend.get_all_tags():
            if tail == tagname:
                st.st_mode = stat.S_IFDIR | 0o555
                st.st_nlink = 2
                return st
        parent_tag = os.path.split(head)[1]
        
        filename, entry_id = self.disassemble_local_name(tail)
        if not filename or not entry_id:
            return errno.ENOENT
        
        entry = backend.get_file_by_id(entry_id)

        if entry is None: 
            return errno.ENOENT
        
        _, _, filepath, _ = entry
        real_st = os.stat(filepath)
        st.st_mode = stat.S_IFLNK | 0o555
        st.st_nlink = real_st.st_nlink
        st.st_size = real_st.st_size
        st.st_uid = real_st.st_uid
        st.st_gid = real_st.st_gid
        st.st_atime = real_st.st_atime
        st.st_mtime = real_st.st_mtime
        st.st_ctime = real_st.st_ctime

        return st

    def readlink(self, path):
        _, local_name = os.path.split(path)
        filename, entry_id = self.disassemble_local_name(local_name)

        entry = backend.get_file_by_id(entry_id)
        if entry is None:
            return ""
        _, _, real_path, _ = entry
        return real_path
    
    def mkdir(self):
        pass
    def rmdir(self):
        pass
                    
def main():
    fuse.fuse_python_api = (0, 2)
    fs = semoFS(version="%prog " + "0", usage=fuse.Fuse.fusage)
    fs.parse(errex=1)
    fs.main()

if __name__ == "__main__":
    main()