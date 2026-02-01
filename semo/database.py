#!/usr/bin/env python3

import sqlite3 as sql

class Database:
    def __init__(self, path : str):
        self.__connection : sql.Connection = sql.connect(path)
        self.__cursor : sql.Cursor = self.__connection.cursor()

    def init_create_script(self):
        self.__cursor.execute("PRAGMA foreign_keys = ON")
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS tag(\
                              id INTEGER PRIMARY KEY, \
                              name VARCHAR(50) NOT NULL UNIQUE\
                              )")
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS file(\
                              id INTEGER PRIMARY KEY, \
                              file_system, \
                              inode INTEGER NOT NULL, \
                              UNIQUE (file_system, inode)\
                              )")
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS rel_file_tag(\
                              id INTEGER PRIMARY KEY, \
                              file_id REFERENCES file ON DELETE CASCADE NOT NULL, \
                              tag_id REFERENCES tag ON DELETE CASCADE NOT NULL\
                              )")
        self.__cursor.execute("CREATE TABLE IF NOT EXISTS rel_tag_tag(\
                              id INTEGER PRIMARY KEY, \
                              superior_id REFERENCES tag ON DELETE CASCADE NOT NULL, \
                              inferior_id REFERENCES tag ON DELETE CASCADE NOT NULL\
                              )")
        
        self.__connection.commit()

    # query functions
    def __get_tag_id(self, tag_name : str) -> int:
        res = self.__cursor.execute("SELECT id FROM tag WHERE name == ?", (tag_name,))
        return res.fetchone()[0]
    def __get_file_id(self, file_system, inode : int) -> int:
        res = self.__cursor.execute("SELECT id FROM file WHERE file_system == ? AND inode == ?", (file_system, inode))
        return res.fetchone()[0]
    def __get_rel_file_tag_id(self, tag_id : int, file_id : int) -> int:
        res = self.__cursor.execute("SELECT id FROM rel_file_tag WHERE tag_id == ? AND file_id == ?", (tag_id, file_id))
        return res.fetchone()
    def __get_rel_tag_tag_id(self, sup_id : int, inf_id : int) -> int:
        res = self.__cursor.execute("SELECT id FROM rel_tag_tag WHERE superior_id == ? AND inferior_id == ?", (sup_id, inf_id))
        return res.fetchone()
    
    def dump_tables(self):
        res = {}
        res["tag"] = self.__cursor.execute("SELECT * FROM tag").fetchall()
        res["file"] = self.__cursor.execute("SELECT * FROM file").fetchall()
        res["rel_file_tag"] = self.__cursor.execute("SELECT * FROM rel_file_tag").fetchall()
        res["rel_tag_tag"] = self.__cursor.execute("SELECT * FROM rel_tag_tag").fetchall()
        return res
    
    
    def list_tags(self) -> list[str]:
        res = self.__cursor.execute ("SELECT name FROM tag")
        return [x[0] for x in res.fetchall()]
    def list_files(self) -> list[int]:
        res = self.__cursor.execute ("SELECT inode FROM file")
        return [x[0] for x in res.fetchall()]
    def list_tags_for_file(self, file_system, inode : int) -> list[str]:
        res = self.__cursor.execute("SELECT tag.name FROM (\
                                        SELECT rel_file_tag.tag_id, rel_file_tag.file_id \
                                        FROM rel_file_tag LEFT JOIN file ON rel_file_tag.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(file_system, inode),))
        return [x[0] for x in res.fetchall()]
    def list_files_for_tag(self, tag_name : str) -> list[tuple[int, int]]:
        # TODO do i have to query tags by id when their name is already unique & not null
        res = self.__cursor.execute("SELECT file.file_system, file.inode FROM (\
                                        SELECT rel_file_tag.tag_id, rel_file_tag.file_id \
                                        FROM rel_file_tag LEFT JOIN tag ON rel_file_tag.tag_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return [(x[0], x[1]) for x in res.fetchall()]
    def list_subtags_for_tag(self, tag_name : str) -> list[str]:
        res = self.__cursor.execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.superior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.inferior_id == tag.id", (self.__get_tag_id(tag_name),))
        return [x[0] for x in res.fetchall()]
    def list_superior_tags_for_tag(self, tag_name : str) -> list[str]:
        res = self.__cursor.execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.inferior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.superior_id == tag.id", (self.__get_tag_id(tag_name),))
        return [x[0] for x in res.fetchall()]
    
    # TODO
    def list_root_tags(self) -> list[str]:
        res = self.__cursor.execute(
            "SELECT tag.name \
            FROM tag LEFT JOIN rel_tag_tag ON tag.id = rel_tag_tag.inferior_id \
            WHERE rel_tag_tag.inferior_id IS NULL"
        )
        return [x[0] for x in res.fetchall()]



    # editing functions TODO return a response
    def new_tag(self, tag_name : str):
        self.__cursor.execute("INSERT INTO tag VALUES (NULL, ?)", (tag_name,))
        self.__connection.commit()
    def delete_tag(self, tag_name : str):
        id_to_delete = self.__get_tag_id(tag_name)
        self.__cursor.execute("DELETE FROM tag WHERE name == ?", (tag_name,))
        self.__cursor.execute("DELETE FROM rel_file_tag WHERE tag_id == ?", (id_to_delete,))
        self.__cursor.execute("DELETE FROM rel_tag_tag WHERE superior_id == ? OR inferior_id == ?", (id_to_delete, id_to_delete))
        self.__connection.commit()

    def new_file(self, file_system, inode : int):
        self.__cursor.execute("INSERT INTO file VALUES (NULL, ?, ?)", (file_system, inode))
        self.__connection.commit()
    def delete_file(self, file_system, inode : int):
        id_to_delete = self.__get_file_id(file_system, inode)
        self.__cursor.execute("DELETE FROM file WHERE file_system == ? AND inode == ?", (file_system, inode))
        self.__cursor.execute("DELETE FROM rel_file_tag WHERE file_id == ?", (id_to_delete,))
        self.__connection.commit()
    
    def new_rel_file_tag(self, file_system, inode : int, tag_name : str):
        self.__cursor.execute("INSERT INTO rel_file_tag VALUES(NULL, ?, ?)", (self.__get_file_id(file_system, inode), self.__get_tag_id(tag_name)))
        self.__connection.commit()
    def delete_rel_file_tag(self, file_system, inode : int, tag_name : str):
        self.__cursor.execute("DELETE FROM rel_file_tag \
                              WHERE file_id == ? \
                              AND tag_id == ?", (self.__get_file_id(file_system, inode), self.__get_tag_id(tag_name)))
        self.__connection.commit()

    def new_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        self.__cursor.execute("INSERT INTO rel_tag_tag VALUES(NULL, ?, ?)", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        self.__connection.commit()
    def delete_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        self.__cursor.execute("DELETE FROM rel_tag_tag \
                              WHERE superior_id == ? \
                              AND inferior_id == ?", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        self.__connection.commit()