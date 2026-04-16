#!.venv/bin/python3

import sqlite3 as sql

class Database:
    def __init__(self, path : str):
        self.__path = path
        conn : sql.Connection = sql.connect(self.__path)
        conn.close()
        # self.__connection : sql.Connection = sql.connect(path)
        # conn.cursor() : sql.Cursor = self.__connection.cursor()
        self.verify_db()

    def __connection(self) -> sql.Connection:
        return sql.connect(self.__path)

    def verify_db(self):
        required_tables = {'tag', 'file', 'rel_file_tag', 'rel_tag_tag'}
        required_indices = {'idx_tag', 'idx_file_inode', 'idx_file_path', 'idx_rel_ft', 'idx_rel_tt'}

        conn = self.__connection()
        res = conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = set(x[0] for x in res.fetchall())
        if len(tables) == 0:
            self.init_create_script()
            return True
        if tables != required_tables:
            return False
        res = conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = set(x[0] for x in res.fetchall())
        if not required_indices <= indices:
            return False
        
        tag_columns = conn.cursor().execute("SELECT name FROM PRAGMA_TABLE_INFO('tag')")
        if set(x[0] for x in tag_columns.fetchall()) != {'id', 'name'}:
            return False
        file_columns = conn.cursor().execute("SELECT name FROM PRAGMA_TABLE_INFO('file')")
        if set(x[0] for x in file_columns.fetchall()) != {'id', 'fsid', 'inode', 'path'}:
            return False
        rel_file_tag_columns = conn.cursor().execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_file_tag')")
        if set(x[0] for x in rel_file_tag_columns.fetchall()) != {'id', 'file_id', 'tag_id'}:
            return False
        rel_tag_tag_columns = conn.cursor().execute("SELECT name FROM PRAGMA_TABLE_INFO('rel_tag_tag')")
        if set(x[0] for x in rel_tag_tag_columns.fetchall()) != {'id', 'superior_id', 'inferior_id'}:
            return False
        
        return True
        
    def init_create_script(self):
        conn = self.__connection()
        conn.cursor().execute("PRAGMA foreign_keys = ON")

        conn.cursor().execute("CREATE TABLE IF NOT EXISTS tag(\
                              id INTEGER PRIMARY KEY, \
                              name VARCHAR(50) NOT NULL UNIQUE\
                              )")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_tag ON tag (name)")

        conn.cursor().execute("CREATE TABLE IF NOT EXISTS file(\
                              id INTEGER PRIMARY KEY, \
                              fsid INTEGER NOT NULL, \
                              inode INTEGER NOT NULL, \
                              path VARCHAR(255), \
                              UNIQUE (fsid, inode)\
                              )")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_file_inode ON file (inode, fsid)")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_file_path ON file (path)")

        conn.cursor().execute("CREATE TABLE IF NOT EXISTS rel_file_tag(\
                              id INTEGER PRIMARY KEY, \
                              file_id REFERENCES file ON DELETE CASCADE NOT NULL, \
                              tag_id REFERENCES tag ON DELETE CASCADE NOT NULL,\
                              UNIQUE (file_id, tag_id) \
                              )")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_rel_ft ON rel_file_tag (file_id)")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_rel_ft ON rel_file_tag (tag_id)")

        conn.cursor().execute("CREATE TABLE IF NOT EXISTS rel_tag_tag(\
                              id INTEGER PRIMARY KEY, \
                              superior_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              inferior_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              CONSTRAINT check_not_duplicate_tag CHECK (superior_id != inferior_id), \
                              UNIQUE (superior_id, inferior_id) \
                              )")
        conn.cursor().execute("CREATE INDEX IF NOT EXISTS idx_rel_tt ON rel_tag_tag (inferior_id, superior_id)")
        
        conn.commit()
        conn.close()

    def clear_contents(self):
        conn = self.__connection()
        conn.cursor().execute("DELETE FROM file")
        conn.cursor().execute("DELETE FROM tag")
        conn.cursor().execute("DELETE FROM rel_file_tag")
        conn.cursor().execute("DELETE FROM rel_tag_tag")
        conn.commit()
        conn.close()

    def __get_tag_id(self, tag_name : str) -> int:
        res = self.__connection().cursor().execute("SELECT id FROM tag WHERE name == ?", (tag_name,))
        return res.fetchone()[0]
    def __get_file_id(self, fsid, inode : int) -> int:
        res = self.__connection().cursor().execute("SELECT id FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        return res.fetchone()[0]
    def __get_rel_file_tag_id(self, tag_id : int, file_id : int) -> int:
        res = self.__connection().cursor().execute("SELECT id FROM rel_file_tag WHERE tag_id == ? AND file_id == ?", (tag_id, file_id))
        return res.fetchone()
    def __get_rel_tag_tag_id(self, sup_id : int, inf_id : int) -> int:
        res = self.__connection().cursor().execute("SELECT id FROM rel_tag_tag WHERE superior_id == ? AND inferior_id == ?", (sup_id, inf_id))
        return res.fetchone()
    
    def dump_tables(self):
        conn = self.__connection()
        res = {}
        res["tag"] = conn.cursor().execute("SELECT * FROM tag").fetchall()
        res["file"] = conn.cursor().execute("SELECT * FROM file").fetchall()
        res["rel_file_tag"] = conn.cursor().execute("SELECT * FROM rel_file_tag").fetchall()
        res["rel_tag_tag"] = conn.cursor().execute("SELECT * FROM rel_tag_tag").fetchall()
        return res
    
    def new_tag(self, tag_name : str):
        conn = self.__connection()
        conn.cursor().execute("INSERT INTO tag VALUES (NULL, ?)", (tag_name,))
        conn.commit()
    def delete_tag(self, tag_name : str):
        conn = self.__connection()
        id_to_delete = self.__get_tag_id(tag_name)
        conn.cursor().execute("DELETE FROM tag WHERE name == ?", (tag_name,))
        conn.cursor().execute("DELETE FROM rel_file_tag WHERE tag_id == ?", (id_to_delete,))
        conn.cursor().execute("DELETE FROM rel_tag_tag WHERE superior_id == ? OR inferior_id == ?", (id_to_delete, id_to_delete))
        conn.commit()

    def new_file(self, fsid : int, inode : int, path : str):
        conn = self.__connection()
        conn.cursor().execute("INSERT INTO file VALUES (NULL, ?, ?, ?)", (fsid, inode, path))
        conn.commit()
    def delete_file(self, fsid : int, inode : int):
        conn = self.__connection()
        id_to_delete = self.__get_file_id(fsid, inode)
        conn.cursor().execute("DELETE FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        conn.cursor().execute("DELETE FROM rel_file_tag WHERE file_id == ?", (id_to_delete,))
        conn.commit()
    
    def new_rel_file_tag(self, fsid : int, inode : int, tag_name : str):
        conn = self.__connection()
        conn.cursor().execute("INSERT INTO rel_file_tag VALUES(NULL, ?, ?)", (self.__get_file_id(fsid, inode), self.__get_tag_id(tag_name)))
        conn.commit()
    def delete_rel_file_tag(self, fsid : int, inode : int, tag_name : str):
        conn = self.__connection()
        conn.cursor().execute("DELETE FROM rel_file_tag \
                              WHERE file_id == ? \
                              AND tag_id == ?", (self.__get_file_id(fsid, inode), self.__get_tag_id(tag_name)))
        conn.commit()

    def new_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        conn = self.__connection()
        conn.cursor().execute("INSERT INTO rel_tag_tag VALUES(NULL, ?, ?)", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        conn.commit()
    def delete_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        conn = self.__connection()
        conn.cursor().execute("DELETE FROM rel_tag_tag \
                              WHERE superior_id == ? \
                              AND inferior_id == ?", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        conn.commit()
        
    # direct queries

    def _direct_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        res = self.__connection().cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_file_tag.tag_id, rel_file_tag.file_id \
                                        FROM rel_file_tag LEFT JOIN file ON rel_file_tag.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0] for x in res.fetchall()}

    def _direct_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        res = self.__connection().cursor().execute("SELECT file.fsid, file.inode, file.path, file.id FROM (\
                                            SELECT rel_file_tag.tag_id, rel_file_tag.file_id \
                                            FROM rel_file_tag LEFT JOIN tag ON rel_file_tag.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                        LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3]) for x in res.fetchall()}

    def _direct_inferiors_for_tag(self, tag_name : str) -> set[str]:
        res = self.__connection().cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.superior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.inferior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    def _direct_superiors_for_tag(self, tag_name : str) -> set[str]:
        res = self.__connection().cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.inferior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.superior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    # query functions
    
    def get_tags(self) -> set[str]:
        res = self.__connection().cursor().execute ("SELECT name FROM tag")
        return set([x[0] for x in res.fetchall()])
    def get_files(self) -> set[tuple[str, int]]:
        res = self.__connection().cursor().execute ("SELECT fsid, inode, path FROM file")
        return set([(x[0], x[1]) for x in res.fetchall()])
    def get_files_with_paths(self) -> set[tuple[str, int, str]]:
        res = self.__connection().cursor().execute ("SELECT fsid, inode, path FROM file")
        return set([(x[0], x[1], x[2]) for x in res.fetchall()])
    
    def get_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        output = set()
        direct_rels = self._direct_tags_for_file(fsid, inode)
        output.update(direct_rels)
        for t in direct_rels:
            output.update(self.get_superiors_tree(t))
        return output
    
    def get_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        output = self._direct_files_for_tag(tag_name)
        for rel in self.get_inferiors_tree(tag_name):
            output.update(self._direct_files_for_tag(rel))
        return output
    
    def get_root_tags(self) -> set[str]:
        res = self.__connection().cursor().execute(
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
    
    # filepaths
    def get_file_path(self, fsid : int, inode : int) -> str:
        res = self.__connection().cursor().execute("SELECT path FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        return res.fetchone()[0]
    def set_file_path(self, fsid : int, inode : int, path : str):
        conn = self.__connection()
        conn.cursor().execute("UPDATE file SET path = ? WHERE fsid == ? AND inode == ?", (path, fsid, inode))
        conn.commit()

    def get_file_entry_from_fsid_inode(self, fsid : int, inode: int):
        res = self.__connection().cursor().execute("SELECT fsid, inode, path FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        if res is not None:
            return res.fetchone()[0]
    def get_file_entry_from_path(self, path: str):
        res = self.__connection().cursor().execute("SELECT fsid, inode, path FROM file WHERE path == ?", (path,))
        if res is not None:
            return res.fetchall()
        
    def get_file_by_id(self, entry_id : int):
        res = self.__connection().cursor().execute("SELECT fsid, inode, path, id FROM file WHERE id == ?", (entry_id,))
        if res is not None:
            return res.fetchone()