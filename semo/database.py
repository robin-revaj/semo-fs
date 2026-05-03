#!.venv/bin/python3

import sqlite3 as sql
from utils import SemoException

class Database:
    def __init__(self, path : str):
        self.__path = path
        self.__conn : sql.Connection = sql.connect(self.__path)
        #conn.close()
        # self.__connection : sql.Connection = sql.connect(path)
        # conn.cursor() : sql.Cursor = self.__connection.cursor()

        if not self.verify_db():
            raise SemoException("Failed database initalization")

    def connect(self):
        self.__conn = sql.connect(self.__path)
    
    def disconnect(self):
        self.__conn.close()

    def verify_db(self):
        required_tables = {'tag', 'file', 'rel_file_tag_null', 'rel_file_tag_str', 'rel_file_tag_int', 'rel_tag_tag', 'filesystem'}
        required_indices = {'idx_tag', 'idx_file_inode', 'idx_file_path', 
                            'idx_rel_ft_f', 'idx_rel_ft_t', 
                            'idx_rel_ft_str_f', 'idx_rel_ft_str_t', 
                            'idx_rel_ft_int_f', 'idx_rel_ft_int_t', 
                            'idx_rel_tt'}

        #conn = self.__connection()
        c = self.__conn.cursor()
        try:
            res = c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = set(x[0] for x in res.fetchall())
            if len(tables) == 0:
                self.init_create_script()
                return True
            if tables != required_tables:
                return False
            res = c.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indices = set(x[0] for x in res.fetchall())
            if not required_indices <= indices:
                return False
            
            tag_columns = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('tag')")
            if set(x[0] for x in tag_columns.fetchall()) != {'id', 'name', 'type'}:
                return False
            file_columns = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('file')")
            if set(x[0] for x in file_columns.fetchall()) != {'id', 'fsid', 'inode', 'path'}:
                return False
            null_rel = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_file_tag_null')")
            if set(x[0] for x in null_rel.fetchall()) != {'id', 'file_id', 'tag_id'}:
                return False
            str_rel = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_file_tag_str')")
            if set(x[0] for x in str_rel.fetchall()) != {'id', 'file_id', 'tag_id', 'value'}:
                return False
            int_rel = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_file_tag_int')")
            if set(x[0] for x in int_rel.fetchall()) != {'id', 'file_id', 'tag_id', 'value'}:
                    return False
            rel_tag_tag_columns = c.execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_tag_tag')")
            if set(x[0] for x in rel_tag_tag_columns.fetchall()) != {'id', 'superior_id', 'inferior_id'}:
                return False
        except Exception as e:
            raise SemoException("Failed database verification", e)
        return True
        
    def init_create_script(self):
        #conn = self.__connection()
        c = self.__conn.cursor()
        c.execute("PRAGMA foreign_keys = ON")

        c.execute("CREATE TABLE IF NOT EXISTS tag(\
                              id INTEGER PRIMARY KEY, \
                              name VARCHAR(50) NOT NULL UNIQUE, \
                              type VARCHAR(3)\
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_tag ON tag (name)")

        c.execute("CREATE TABLE IF NOT EXISTS file(\
                              id INTEGER PRIMARY KEY, \
                              fsid INTEGER NOT NULL, \
                              inode INTEGER NOT NULL, \
                              path VARCHAR(255), \
                              UNIQUE (fsid, inode)\
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_file_inode ON file (inode, fsid)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_file_path ON file (path)")

        c.execute("CREATE TABLE IF NOT EXISTS rel_file_tag_null(\
                              id INTEGER PRIMARY KEY, \
                              file_id REFERENCES file ON DELETE CASCADE NOT NULL, \
                              tag_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              UNIQUE (file_id, tag_id) \
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_f ON rel_file_tag_null (file_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_t ON rel_file_tag_null (tag_id)")

        c.execute("CREATE TABLE IF NOT EXISTS rel_file_tag_str(\
                              id INTEGER PRIMARY KEY, \
                              file_id REFERENCES file ON DELETE CASCADE NOT NULL, \
                              tag_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              value STRING, \
                              UNIQUE (file_id, tag_id) \
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_str_f ON rel_file_tag_str (file_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_str_t ON rel_file_tag_str (tag_id)")

        c.execute("CREATE TABLE IF NOT EXISTS rel_file_tag_int(\
                              id INTEGER PRIMARY KEY, \
                              file_id REFERENCES file ON DELETE CASCADE NOT NULL, \
                              tag_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              value INTEGER, \
                              UNIQUE (file_id, tag_id) \
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_int_f ON rel_file_tag_int (file_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_ft_int_t ON rel_file_tag_int (tag_id)")

        c.execute("CREATE TABLE IF NOT EXISTS rel_tag_tag(\
                              id INTEGER PRIMARY KEY, \
                              superior_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              inferior_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              CONSTRAINT check_not_duplicate_tag CHECK (superior_id != inferior_id), \
                              UNIQUE (superior_id, inferior_id) \
                              )")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rel_tt ON rel_tag_tag (inferior_id, superior_id)")
        
        c.execute("CREATE TABLE IF NOT EXISTS filesystem(\
                              id INTEGER PRIMARY KEY, \
                              fsid INTEGER NOT NULL UNIQUE,\
                              active BOOLEAN NOT NULL DEFAULT true \
                              )")

        self.__conn.commit()
        #conn.close()

    def clear_contents(self):
        #conn = self.__connection()
        c = self.__conn.cursor()
        c.execute("DELETE FROM file")
        c.execute("DELETE FROM tag")
        c.execute("DELETE FROM rel_file_tag_null")
        c.execute("DELETE FROM rel_file_tag_str")
        c.execute("DELETE FROM rel_file_tag_int")
        c.execute("DELETE FROM rel_tag_tag")
        self.__conn.commit()
        # conn.commit()
        # conn.close()

    def __get_tag_id(self, tag_name : str) -> int | None:
        res = self.__conn.cursor().execute("SELECT id FROM tag WHERE name == ?", (tag_name,))
        try:
            return res.fetchone()[0]
        except TypeError:
            return None
    def __get_file_id(self, fsid : int, inode : int) -> int | None:
        res = self.__conn.cursor().execute("SELECT id FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        try:
            return res.fetchone()[0]
        except TypeError:
            return None
    def __get_rel_file_tag_null_id(self, tag_id : int, file_id : int) -> int:
        res = self.__conn.cursor().execute("SELECT id FROM rel_file_tag_null WHERE tag_id == ? AND file_id == ?", (tag_id, file_id))
        return res.fetchone()
    def __get_rel_file_tag_str_id(self, tag_id : int, file_id : int) -> int:
        res = self.__conn.cursor().execute("SELECT id FROM rel_file_tag_str WHERE tag_id == ? AND file_id == ?", (tag_id, file_id))
        return res.fetchone()
    def __get_rel_file_tag_int_id(self, tag_id : int, file_id : int) -> int:
        res = self.__conn.cursor().execute("SELECT id FROM rel_file_tag_int WHERE tag_id == ? AND file_id == ?", (tag_id, file_id))
        return res.fetchone()
    def __get_rel_tag_tag_id(self, sup_id : int, inf_id : int) -> int:
        res = self.__conn.cursor().execute("SELECT id FROM rel_tag_tag WHERE superior_id == ? AND inferior_id == ?", (sup_id, inf_id))
        return res.fetchone()

    def dump_tables(self):
        #conn = self.__connection()
        c = self.__conn.cursor()
        res = {}
        res["tag"] = c.execute("SELECT * FROM tag").fetchall()
        res["file"] = c.execute("SELECT * FROM file").fetchall()
        res["rel_file_tag_null"] = c.execute("SELECT * FROM rel_file_tag_null").fetchall()
        res["rel_file_tag_str"] = c.execute("SELECT * FROM rel_file_tag_str").fetchall()
        res["rel_file_tag_int"] = c.execute("SELECT * FROM rel_file_tag_int").fetchall()
        res["rel_tag_tag"] = c.execute("SELECT * FROM rel_tag_tag").fetchall()
        return res
    
    def new_tag(self, tag_name : str, tag_type = None):
        if self.__get_tag_id(tag_name): raise SemoException("tag already in database")
        #conn = self.__connection()
        self.__conn.cursor().execute("INSERT INTO tag VALUES (NULL, ?, ?)", (tag_name, tag_type))
        self.__conn.commit()
    def delete_tag(self, tag_name : str):
        #conn = self.__connection()
        id_to_delete = self.__get_tag_id(tag_name)
        if not id_to_delete:
            raise SemoException("tag not in database")
        tag_type = self.get_tag_type(tag_name)
        c = self.__conn.cursor()
        c.execute("DELETE FROM tag WHERE name == ?", (tag_name,))
        c.execute("DELETE FROM rel_tag_tag WHERE superior_id == ? OR inferior_id == ?", (id_to_delete, id_to_delete))
        match (tag_type):
            case "str":
                c.execute("DELETE FROM rel_file_tag_str WHERE tag_id == ?", (id_to_delete,))
            case "int":
                c.execute("DELETE FROM rel_file_tag_int WHERE tag_id == ?", (id_to_delete,))
            case _:
                c.execute("DELETE FROM rel_file_tag_null WHERE tag_id == ?", (id_to_delete,))
        self.__conn.commit()

    def new_file(self, fsid : int, inode : int, path : str):
        if self.__get_file_id(fsid, inode): raise SemoException("file already in database")
        #conn = self.__connection()
        c = self.__conn.cursor()
        c.execute("INSERT INTO file VALUES (NULL, ?, ?, ?)", (fsid, inode, path))
        c.execute("INSERT OR IGNORE INTO filesystem VALUES (NULL, ?, ?)", (fsid, True))
        self.__conn.commit()
    def delete_file(self, fsid : int, inode : int, id=None):
        #conn = self.__connection()
        if id is None:
            id_to_delete = self.__get_file_id(fsid, inode)
        else:
            id_to_delete = id
        if not id_to_delete:
            raise SemoException("file not in database")
        c = self.__conn.cursor()
        c.execute("DELETE FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        c.execute("DELETE FROM rel_file_tag_str WHERE file_id == ?", (id_to_delete,))
        c.execute("DELETE FROM rel_file_tag_int WHERE file_id == ?", (id_to_delete,))
        c.execute("DELETE FROM rel_file_tag_null WHERE file_id == ?", (id_to_delete,))
        self.__conn.commit()
    
    def __new_rel_file_tag_null(self, file_id : int, tag_id : int):
        #conn = self.__connection()
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_null VALUES(NULL, ?, ?)", (file_id, tag_id))
        self.__conn.commit()
    def __delete_rel_file_tag_null(self, file_id : int, tag_id : int):
        #conn = self.__connection()
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_null \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def __new_rel_file_tag_str(self, file_id : int, tag_id : int, value : str):
        #conn = self.__connection()
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_str VALUES(NULL, ?, ?, ?)", (file_id, tag_id, value))
        self.__conn.commit()
    def __delete_rel_file_tag_str(self, file_id : int, tag_id : int):
        #conn = self.__connection()
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_str \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def __new_rel_file_tag_int(self, file_id : int, tag_id : int, value : int):
        #conn = self.__connection()
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_int VALUES(NULL, ?, ?, ?)", (file_id, tag_id, value))
        self.__conn.commit()
    def __delete_rel_file_tag_int(self, file_id : int, tag_id : int):
        #conn = self.__connection()
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_int \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def new_rel_file_tag(self, fsid : int, inode : int, tag_name : str, value = None):
        file_id, tag_id = self.__get_file_id(fsid, inode), self.__get_tag_id(tag_name)
        if not file_id or not tag_id: raise SemoException("file or tag not in database")
        
        match self.get_tag_type(tag_name):
            case "str":
                if self.__get_rel_file_tag_str_id(tag_id, file_id): raise SemoException("relationship already in database")
                if not isinstance(value, str): raise SemoException("wrong value type")
                self.__new_rel_file_tag_str(file_id, tag_id, value)
            case "int":
                if self.__get_rel_file_tag_int_id(tag_id, file_id): raise SemoException("relationship already in database")
                if not isinstance(value, int): raise SemoException("wrong value type")
                self.__new_rel_file_tag_int(file_id, tag_id, value)
            case _:
                if self.__get_rel_file_tag_null_id(tag_id, file_id): raise SemoException("relationship already in database")
                #if value is not None: raise SemoException("wrong value type")
                self.__new_rel_file_tag_null(file_id, tag_id)

    def delete_rel_file_tag(self, fsid : int, inode : int, tag_name : str):
        file_id, tag_id = self.__get_file_id(fsid, inode), self.__get_tag_id(tag_name)
        if not file_id or not tag_id: raise SemoException("file or tag not in database")
        match self.get_tag_type(tag_name):
            case "str":
                self.__delete_rel_file_tag_str(file_id, tag_id)
            case "int":
                self.__delete_rel_file_tag_int(file_id, tag_id)
            case _:
                self.__delete_rel_file_tag_null(file_id, tag_id)

    def new_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        sup_id, inf_id = self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)
        if not sup_id or not inf_id: raise SemoException("superior or inferior tag not in database")
        if self.__get_rel_tag_tag_id(sup_id, inf_id): raise SemoException("relationship aready in database")
        #conn = self.__connection()
        self.__conn.cursor().execute("INSERT INTO rel_tag_tag VALUES(NULL, ?, ?)", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        self.__conn.commit()
    def delete_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        #conn = self.__connection()
        self.__conn.cursor().execute("DELETE FROM rel_tag_tag \
                              WHERE superior_id == ? \
                              AND inferior_id == ?", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        self.__conn.commit()
        
    # direct queries

    def __direct_null_rels_for_file(self, fsid : int, inode : int) -> set[str]:
        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_file_tag_null.tag_id, rel_file_tag_null.file_id \
                                        FROM rel_file_tag_null LEFT JOIN file ON rel_file_tag_null.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0] for x in res.fetchall()}
    
    def __direct_str_rels_for_file(self, fsid : int, inode : int) -> dict[str, str]: 
        res = self.__conn.cursor().execute("SELECT tag.name, r.value FROM (\
                                        SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                        FROM rel_file_tag_str LEFT JOIN file ON rel_file_tag_str.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0]:x[1] for x in res.fetchall()}
    
    def __direct_int_rels_for_file(self, fsid : int, inode : int) -> dict[str, int]: 
        res = self.__conn.cursor().execute("SELECT tag.name, r.value FROM (\
                                        SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                        FROM rel_file_tag_int LEFT JOIN file ON rel_file_tag_int.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0]:x[1] for x in res.fetchall()}
    
    def _direct_rels_for_file(self, fsid : int, inode : int) -> dict:
        null_rels = {rel : None for rel in self.__direct_null_rels_for_file(fsid, inode)}
        str_rels = self.__direct_str_rels_for_file(fsid, inode)
        int_rels = self.__direct_int_rels_for_file(fsid, inode)
        combined = {}
        combined.update(null_rels)
        combined.update(str_rels)
        combined.update(int_rels)
        return combined
    
    def _direct_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        return set(self._direct_rels_for_file(fsid, inode).keys())

    def _direct_null_rels_for_tag(self, tag_name : str) -> set[tuple]:
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id FROM (\
                                            SELECT rel_file_tag_null.tag_id, rel_file_tag_null.file_id \
                                            FROM rel_file_tag_null LEFT JOIN tag ON rel_file_tag_null.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                        LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], tag_name) for x in res.fetchall()}
    
    def _direct_str_rels_for_tag(self, tag_name : str) -> set[tuple]:
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                            FROM rel_file_tag_str LEFT JOIN tag ON rel_file_tag_str.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                        LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, x[4]])) for x in res.fetchall()}


    def _str_rels_for_tag_condition(self, tag_name : str, condition : str) -> set[tuple]:
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                            FROM rel_file_tag_str LEFT JOIN tag ON rel_file_tag_str.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id \
                                            WHERE r.value == ?", (self.__get_tag_id(tag_name), condition))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, x[4]])) for x in res.fetchall()}
    
    def _direct_int_rels_for_tag(self, tag_name : str) -> set[tuple]:
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                            FROM rel_file_tag_int LEFT JOIN tag ON rel_file_tag_int.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, str(x[4])])) for x in res.fetchall()}
    
    def _int_rels_for_tag_condition(self, tag_name : str, operator : str, condition : int) -> set[tuple]:
        if operator not in ["==", ">", "<", ">=", "<="]:
            raise SemoException("invalid condition operator")
        res = self.__conn.cursor().execute(f"SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                            FROM rel_file_tag_int LEFT JOIN tag ON rel_file_tag_int.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id \
                                            WHERE r.value {operator} ?", (self.__get_tag_id(tag_name), condition))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, str(x[4])])) for x in res.fetchall()}
    
    def _direct_rels_for_tag(self, tag_name : str) -> set[tuple]:
        tag_type = self.get_tag_type(tag_name)
        match tag_type:
            case "str":
                return self._direct_str_rels_for_tag(tag_name)
            case "int":
                return self._direct_int_rels_for_tag(tag_name)
        return self._direct_null_rels_for_tag(tag_name)

    def _direct_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        return {x[0:4] for x in self._direct_rels_for_tag(tag_name)}
        # res = self.__connection().cursor().execute("SELECT file.fsid, file.inode, file.path, file.id FROM (\
        #                                     SELECT rel_file_tag_null.tag_id, rel_file_tag_null.file_id \
        #                                     FROM rel_file_tag_null LEFT JOIN tag ON rel_file_tag_null.tag_id == tag.id\
        #                                     WHERE tag.id == ?) AS r\
        #                                 LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        # return {(x[0], x[1], x[2], x[3]) for x in res.fetchall()}
    
    def _direct_inferiors_for_tag(self, tag_name : str) -> set[str]:
        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.superior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.inferior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    def _direct_superiors_for_tag(self, tag_name : str) -> set[str]:
        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.inferior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.superior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    # query functions
    
    def get_tags(self) -> set[str]:
        res = self.__conn.cursor().execute ("SELECT name FROM tag")
        return set([x[0] for x in res.fetchall()])
    def get_files(self) -> set[tuple[int, int]]:
        res = self.__conn.cursor().execute ("SELECT fsid, inode, path FROM file")
        return set([(x[0], x[1]) for x in res.fetchall()])
    def get_files_with_paths(self) -> set[tuple[int, int, str, int]]:
        res = self.__conn.cursor().execute ("SELECT fsid, inode, path, id FROM file")
        return set([(x[0], x[1], x[2], x[3]) for x in res.fetchall()])
    
    def get_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        output = set()
        direct_tags = self._direct_tags_for_file(fsid, inode)
        output.update(direct_tags)
        for tag_name in direct_tags:
            output.update(self.get_superiors_tree(tag_name))
        return output
    
    def get_rels_for_file(self, fsid : int, inode : int) -> dict[str, str | int | None]:
        output = {}
        direct_rels = self._direct_rels_for_file(fsid, inode)
        output.update(direct_rels)
        for tag_name in direct_rels.keys():
            output.update({superior : None for superior in self.get_superiors_tree(tag_name)})
        return output
    
    def get_tag_type(self, tag_name : str) -> str:
        res = self.__conn.cursor().execute("SELECT type FROM tag WHERE name == ?", (tag_name,))
        return res.fetchone()[0]
    
    def get_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        output = self._direct_files_for_tag(tag_name)
        for rel in self.get_inferiors_tree(tag_name):
            output.update(self._direct_files_for_tag(rel))
        return output
    
    def get_rels_for_tag(self, tag_name : str) -> set:
        output = set()
        direct_rels = self._direct_rels_for_tag(tag_name)
        output.update(direct_rels)
        for rel in self.get_inferiors_tree(tag_name):
            output.update(self._direct_rels_for_tag(rel))
        return output
    
    def get_root_tags(self) -> set[str]:
        res = self.__conn.cursor().execute(
            "SELECT tag.name \
            FROM tag LEFT JOIN rel_tag_tag ON tag.id = rel_tag_tag.inferior_id \
            WHERE rel_tag_tag.inferior_id IS NULL"
        )
        return set([x[0] for x in res.fetchall()])
    
    def get_inferiors_tree(self, tag_name : str) -> set[str]:
        output = set()
        queue = [tag_name]
        while queue:
            current = queue.pop()
            res = self._direct_inferiors_for_tag(current)
            queue.extend(res)
            output.update(res)
        return output

    def get_superiors_tree(self, tag_name : str) -> set[str]:
        output = set()
        queue = [tag_name]
        while queue:
            current = queue.pop()
            res = self._direct_superiors_for_tag(current)
            queue.extend(res)
            output.update(res)
        return output
    
    # file management
    def get_file_path(self, fsid : int, inode : int) -> str:
        res = self.__conn.cursor().execute("SELECT path FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        return res.fetchone()[0]
    def set_file_path(self, fsid : int, inode : int, path : str):
        #conn = self.__connection()
        self.__conn.cursor().execute("UPDATE file SET path = ? WHERE fsid == ? AND inode == ?", (path, fsid, inode))
        self.__conn.commit()
    def set_file_fsid_inode(self, fsid : int, inode : int, filepath : str):
        self.__conn.cursor().execute("UPDATE file SET fsid = ?, inode = ? WHERE path == ?", (fsid, inode, filepath))
        self.__conn.commit()
    def get_file_by_fsid_inode(self, fsid : int, inode: int):
        res = self.__conn.cursor().execute("SELECT fsid, inode, path FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        if res is not None:
            return res.fetchone()[0]
    def get_file_by_path(self, path: str):
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path == ?", (path,))
        try:
            return res.fetchall()[0]
        except IndexError:
            return None
    def get_files_by_path_prefix(self, path_prefix: str) :
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path LIKE ?", (path_prefix + '%',))
        if res is not None:
            return res.fetchall()
        return []
    def get_files_by_path_suffix(self, path_suffix: str) :
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path LIKE ?", ('%' + path_suffix,))
        if res is not None:
            return res.fetchall()
        return []
    def get_file_by_id(self, entry_id : int):
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE id == ?", (entry_id,))
        if res is not None:
            return res.fetchone()
        
    def is_known_and_is_awake_fs(self, fsid : int) -> bool | None:
        res = self.__conn.cursor().execute("SELECT active FROM filesystem WHERE fsid == ?", (fsid,))
        try:
            return res.fetchone()[0]
        except TypeError:
            return 
    def set_fs_active(self, fsid : int, active : bool = True):
        self.__conn.cursor().execute("INSERT OR IGNORE INTO filesystem VALUES (NULL, ?, ?)", (fsid, active))
        self.__conn.cursor().execute("UPDATE filesystem SET active = ? WHERE fsid == ?", (active, fsid))
        self.__conn.commit()
    def set_fs_sleep(self, fsid : int):
        self.set_fs_active(fsid, False)
    