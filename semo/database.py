#! /usr/bin/env python3

"""Handle all direct interactions with the SQL database.

File should be imported as a module.

Contains the following classes:

    * Database
"""

import sqlite3 as sql
from utils import SemoException

class Database:
    """Wrapper for interacting with a database file.

    Attributes
    ----------
    __path : str
        Path to database file.
    __conn : sql.Connection
        Opened connection created when an instance of class is created.
    
    Methods
    -------
    connect()
        Open new connection under self.__conn.
    disconnect()
        Close connection under self.__conn.
    verify_db()
        Check that the database file contains the correct tables, columns, indices.
    init_create_script()
        Run create script, assemble semo database in empty database file.
    clear_contents()
        Delete all entries from all tables.
    dump_tables()
        Return full contents of all tables as dictionary.
    new_tag(tag_name, tag_type)
        Create new tag entry.
    delete_tag(tag_name)
        Delete tag entry.
    new_file(fsid, inode, path)
        Create new file entry.
    delete_file(fsid, inode, id)
        Delete file entry.
    new_rel_file_tag(fsid, inode, tag_name, value)
        Create new file-tag relationship entry.
    delete_rel_file_tag(fsid, inode, tag_name)
        Delete file-tag relationship entry.
    new_rel_tag_tag(superior_tag, inferior_tag)
        Create new tag-subtag relationship entry.
    delete_rel_tag_tag(superior_tag, inferior_tag)
        Delete tag-subtag relationship entry.
    _direct_rels_for_file(fsid, inode)
        Return direct relationships for file.
    _direct_tags_for_file(fsid, inode)
        Return tag names of direct relationships for file.
    _direct_null_rels_for_tag(tag_name)
    _direct_str_rels_for_tag(tag_name)
    _direct_int_rels_for_tag(tag_name)
    _str_rels_for_tag_condition(tag_name, condition)
    _int_rels_for_tag_condition(tag_name, operator, condition)
    _direct_rels_for_tag(tag_name)
        Return direct relationships for tag.
    _direct_files_for_tag(tag_name)
        Return file data of direct relationships for tag.
    _direct_inferiors_for_tag(tag_name)
        Return direct tag-subtag relationships where given tag is the superior.
    _direct_superiors_for_tag(tag_name)
        Return direct tag-subtag relationships where given tag is the inferior.
    get_tags
        Return all tag entries.
    get_files
        Return all file entries, shortened to (fsid, inode).
    get_complete_file_entries
        Return all file entries including the path and id column (fsid, inode, path, id).
    get_rels_for_file(fsid, inode)
        Return direct and inherited file-tag relationships for file.
    get_tags_for_file(fsid, inode)
        Return tag names of direct and inherited file-tag relationships for file.
    get_rels_for_tag(tag_name)
        Return direct and inherited file-tag relationships for tag.
    get_files_for_tag(tag_name)
        Return file data of direct and inherited file-tag relationships for tag.
    get_tag_type(tag_name)
        Return representation of tag's data type.
    get_root_tags()
        Return tags which have no superiors.
    get_inferiors_tree(tag_name)
        Return set of all direct and indirect subtags for tag.
    get_superiors_tree(tag_name)
        Return set of all direct and indirect superior tags for tag.
    set_file_path(fsid, inode, path)
    set_file_fsi_inode(fsid, inode, path)
    get_file_by_fsid_inode(fsid, inode)
    get_file_by_path(path)
    get_file_by_id(entry_id)
    get_files_by_path_prefix(path_prefix)
    get_files_by_path_suffix(path_suffix)
    is_known_and_is_awake_fs(fsid)
    set_fs_active(fsid, active)
    set_fs_sleep(fsid)
    """
    
    def __init__(self, path : str):
        """Create instance of `semo.Database` class.
        
        Initializes object and instantiates SQL connection with file at provided location.

        Then calls class method `verify_db`, which assesses whether the file is compatible with class.

        Raises
        ------
        semo.SemoException
            If file fails verification or errors occur.
        """
        self.__path = path
        self.__conn : sql.Connection = sql.connect(self.__path)
        if not self.verify_db():
            raise SemoException("Failed database initalization")

    def connect(self):
        """Open new connection under `self.__conn`."""

        self.__conn = sql.connect(self.__path)
    
    def disconnect(self):
        """Close connection under `self.__conn`."""

        self.__conn.close()

    def verify_db(self) -> bool:
        """Check if the database file contains the correct tables, columns, indices. 
        
        Returns
        -------
        bool

        Raises
        ------
        SemoException
            in case of SQL error during verification
        """

        required_tables = {'tag', 'file', 'rel_file_tag_null', 'rel_file_tag_str', 'rel_file_tag_int', 'rel_tag_tag', 'filesystem'}
        required_indices = {'idx_tag', 'idx_file_inode', 'idx_file_path', 
                            'idx_rel_ft_f', 'idx_rel_ft_t', 
                            'idx_rel_ft_str_f', 'idx_rel_ft_str_t', 
                            'idx_rel_ft_int_f', 'idx_rel_ft_int_t', 
                            'idx_rel_tt'}

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
        """Run create script which assembles the semo database in an empty database file."""
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

    def clear_contents(self):
        """Delete all entries from all tables."""

        c = self.__conn.cursor()
        c.execute("DELETE FROM file")
        c.execute("DELETE FROM tag")
        c.execute("DELETE FROM rel_file_tag_null")
        c.execute("DELETE FROM rel_file_tag_str")
        c.execute("DELETE FROM rel_file_tag_int")
        c.execute("DELETE FROM rel_tag_tag")
        c.execute("DELETE FROM filesystem")
        self.__conn.commit()

    def dump_tables(self):
        """Return full contents of all tables as dictionary.
        
        Returns
        -------
        dict of {str : list}
        """
        c = self.__conn.cursor()
        res = {}
        res["tag"] = c.execute("SELECT * FROM tag").fetchall()
        res["file"] = c.execute("SELECT * FROM file").fetchall()
        res["rel_file_tag_null"] = c.execute("SELECT * FROM rel_file_tag_null").fetchall()
        res["rel_file_tag_str"] = c.execute("SELECT * FROM rel_file_tag_str").fetchall()
        res["rel_file_tag_int"] = c.execute("SELECT * FROM rel_file_tag_int").fetchall()
        res["rel_tag_tag"] = c.execute("SELECT * FROM rel_tag_tag").fetchall()
        res["filesystem"] = c.execute("SELECT * FROM filesystem").fetchall()
        return res

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

    def new_tag(self, tag_name : str, tag_type = None):
        """Create new tag entry.

        Parameters
        ----------
        tag_name : str
            Name of tag.
        tag_type : {'str', 'int'}, optional
            Data type of the tag's relationship values.
        
        Raises
        ------
        semo.SemoException
            If tag entry already exists.
        """

        if self.__get_tag_id(tag_name): raise SemoException("tag already in database")

        self.__conn.cursor().execute("INSERT INTO tag VALUES (NULL, ?, ?)", (tag_name, tag_type))
        self.__conn.commit()

    def delete_tag(self, tag_name : str):
        """Delete tag entry and its relationships.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.

        Raises
        ------
        semo.SemoException
            If tag entry doesn't exist.
        """

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
        """Create new file entry.

        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.
        path : str
            Path to file.
        
        Raises
        ------
        semo.SemoException
            If file entry already exists.
        """

        if self.__get_file_id(fsid, inode): raise SemoException("file already in database")

        c = self.__conn.cursor()
        c.execute("INSERT INTO file VALUES (NULL, ?, ?, ?)", (fsid, inode, path))
        c.execute("INSERT OR IGNORE INTO filesystem VALUES (NULL, ?, ?)", (fsid, True))
        self.__conn.commit()

    def delete_file(self, fsid : int, inode : int, id=None):
        """Delete file entry and its relationships.

        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.
        id : int, optional
            Internal database ID of file. If set, will be used to identify entry.
        
        Raises
        ------
        semo.SemoException
            If file entry doesn't exist.
        """

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
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_null VALUES(NULL, ?, ?)", (file_id, tag_id))
        self.__conn.commit()
    def __delete_rel_file_tag_null(self, file_id : int, tag_id : int):
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_null \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def __new_rel_file_tag_str(self, file_id : int, tag_id : int, value : str):
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_str VALUES(NULL, ?, ?, ?)", (file_id, tag_id, value))
        self.__conn.commit()
    def __delete_rel_file_tag_str(self, file_id : int, tag_id : int):
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_str \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def __new_rel_file_tag_int(self, file_id : int, tag_id : int, value : int):
        self.__conn.cursor().execute("INSERT INTO rel_file_tag_int VALUES(NULL, ?, ?, ?)", (file_id, tag_id, value))
        self.__conn.commit()
    def __delete_rel_file_tag_int(self, file_id : int, tag_id : int):
        self.__conn.cursor().execute("DELETE FROM rel_file_tag_int \
                              WHERE file_id == ? \
                              AND tag_id == ?", (file_id, tag_id))
        self.__conn.commit()

    def new_rel_file_tag(self, fsid : int, inode : int, tag_name : str, value = None):
        """Create new file-tag relationship entry.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.
        tag_name : str
            Name of tag.
        value : str or int, optional
            Value for relationship.

        Raises
        ------
        semo.SemoException
            If file entry or tag entry don't exist or provided value is not of corresponding data type to provided tag.
        """
        
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
                if value is not None: raise SemoException("wrong value type")
                self.__new_rel_file_tag_null(file_id, tag_id)

    def delete_rel_file_tag(self, fsid : int, inode : int, tag_name : str):
        """Delete file-tag relationship entry.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.
        tag_name : str
            Name of tag.

        Raises
        ------
        semo.SemoException
            If file entry or tag entry don't exist.
        """
        
        file_id, tag_id = self.__get_file_id(fsid, inode), self.__get_tag_id(tag_name)
        if file_id is None or tag_id is None: raise SemoException("file or tag not in database")
        match self.get_tag_type(tag_name):
            case "str":
                self.__delete_rel_file_tag_str(file_id, tag_id)
            case "int":
                self.__delete_rel_file_tag_int(file_id, tag_id)
            case _:
                self.__delete_rel_file_tag_null(file_id, tag_id)

    def new_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        """Create new tag-subtag relationship entry.
        
        Parameters
        ----------
        superior_tag : str
            Name of tag to assign as superior.
        inferior_tag : str
            Name of tag to assign as inferior.

        Raises
        ------
        semo.SemoException
            If superior tag entry or inferior tag entry don't exist.
        """
        
        sup_id, inf_id = self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)
        if not sup_id or not inf_id: raise SemoException("superior or inferior tag not in database")
        if self.__get_rel_tag_tag_id(sup_id, inf_id): raise SemoException("relationship aready in database")
        self.__conn.cursor().execute("INSERT INTO rel_tag_tag VALUES(NULL, ?, ?)", (self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)))
        self.__conn.commit()
    def delete_rel_tag_tag(self, superior_tag : str, inferior_tag : str):
        """Delete tag-subtag relationship entry.
        
        Parameters
        ----------
        superior_tag : str
            Name of superior tag.
        inferior_tag : str
            Name of inferior tag.

        Raises
        ------
        semo.SemoException
            If superior tag entry or inferior tag entry don't exist.
        """

        sup_id, inf_id = self.__get_tag_id(superior_tag), self.__get_tag_id(inferior_tag)
        if not sup_id or not inf_id: raise SemoException("superior or inferior tag not in database")
        self.__conn.cursor().execute("DELETE FROM rel_tag_tag \
                              WHERE superior_id == ? \
                              AND inferior_id == ?", (sup_id, inf_id))
        self.__conn.commit()
        
    # direct queries

    def __direct_null_rels_for_file(self, fsid : int, inode : int) -> set[str]:
        """Return direct relationships for file with tags of NULL data type.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.

        Returns
        -------
        set of str
            Set of tag names.
        """

        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_file_tag_null.tag_id, rel_file_tag_null.file_id \
                                        FROM rel_file_tag_null LEFT JOIN file ON rel_file_tag_null.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0] for x in res.fetchall()}
    
    def __direct_str_rels_for_file(self, fsid : int, inode : int) -> dict[str, str]: 
        """Return direct relationships for file with tags of STR data type.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.

        Returns
        -------
        dict of {str : str}
            Dictionairy of (tag_name : value) pairs.
        """
        
        res = self.__conn.cursor().execute("SELECT tag.name, r.value FROM (\
                                        SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                        FROM rel_file_tag_str LEFT JOIN file ON rel_file_tag_str.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0]:x[1] for x in res.fetchall()}
    
    def __direct_int_rels_for_file(self, fsid : int, inode : int) -> dict[str, int]: 
        """Return direct relationships for file with tags of INT data type.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.

        Returns
        -------
        dict of {str : int}
            Dictionairy of (tag_name : value) pairs.
        """
        
        res = self.__conn.cursor().execute("SELECT tag.name, r.value FROM (\
                                        SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                        FROM rel_file_tag_int LEFT JOIN file ON rel_file_tag_int.file_id == file.id\
                                        WHERE file.id == ?) AS r\
                                    LEFT JOIN tag ON r.tag_id == tag.id", (self.__get_file_id(fsid, inode),))
        return {x[0]:x[1] for x in res.fetchall()}
    
    def _direct_rels_for_file(self, fsid : int, inode : int) -> dict[str, str | int | None]:
        """Return direct file-tag relationships for file.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.

        Returns
        -------
        dict of {str : str, int or None}
            Dictionairy of (tag_name : value) pairs.
        """
        null_rels = {rel : None for rel in self.__direct_null_rels_for_file(fsid, inode)}
        str_rels = self.__direct_str_rels_for_file(fsid, inode)
        int_rels = self.__direct_int_rels_for_file(fsid, inode)
        combined = {}
        combined.update(null_rels)
        combined.update(str_rels)
        combined.update(int_rels)
        return combined
    
    def _direct_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        """Return tag names of direct file-tag relationships for file.
        
        Parameters
        ----------
        fsid : int
            File system ID of file system containing file.
        inode : int
            Index node of file.

        Returns
        -------
        set of str
            Set of tag names.
        """

        return set(self._direct_rels_for_file(fsid, inode).keys())

    def _direct_null_rels_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int, str]]:
        """Return direct file-tag relationships for tag of data type NULL.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Set of tuples containing (fsid, inode, filepath, file entry id, tag name).
        """
        
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id FROM (\
                                            SELECT rel_file_tag_null.tag_id, rel_file_tag_null.file_id \
                                            FROM rel_file_tag_null LEFT JOIN tag ON rel_file_tag_null.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                        LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], tag_name) for x in res.fetchall()}
    
    def _direct_str_rels_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int, str]]:
        """Return direct file-tag relationships for tag of data type STR.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Set of tuples containing (fsid, inode, filepath, file entry id, tag name + value).
        """

        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                            FROM rel_file_tag_str LEFT JOIN tag ON rel_file_tag_str.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                        LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, x[4]])) for x in res.fetchall()}


    def _str_rels_for_tag_condition(self, tag_name : str, condition : str) -> set[tuple[int, int, str, int, str]]:
        """Returns direct file-tag relationships for tag of data type STR where value == condition.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.
        condition : str
            String to be compared against the values of relationships of tag `tag_name`.

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Set of tuples containing (fsid, inode, filepath, file entry id, tag name + value).
        """
        
        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_str.tag_id, rel_file_tag_str.file_id, rel_file_tag_str.value \
                                            FROM rel_file_tag_str LEFT JOIN tag ON rel_file_tag_str.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id \
                                            WHERE r.value == ?", (self.__get_tag_id(tag_name), condition))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, x[4]])) for x in res.fetchall()}
    
    def _direct_int_rels_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int, str]]:
        """Return direct file-tag relationships for tag of data type INT.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Set of tuples containing (fsid, inode, filepath, file entry id, tag name).
        """

        res = self.__conn.cursor().execute("SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                            FROM rel_file_tag_int LEFT JOIN tag ON rel_file_tag_int.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id", (self.__get_tag_id(tag_name),))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, str(x[4])])) for x in res.fetchall()}
    
    def _int_rels_for_tag_condition(self, tag_name : str, operator : str, condition : int) -> set[tuple[int, int, str, int, str]]:
        """Return direct file-tag relationships for tag of data type INT where given condition is met.
        
        Parameters
        ----------
        tag_name : str
            Name of tag.
        operator : {'==', '>', '<', '>=', '<='}
            The integer comparison operator for requested operation.
        condition : int
            Integer to be compared against the values of relationships of tag `tag_name`.

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Set of tuples containing (fsid, inode, filepath, file entry id, tag name).

        Raises
        ------
        semo.SemoException
            If provided `operator` is invalid.
        """
        
        if operator not in ["==", ">", "<", ">=", "<="]:
            raise SemoException("invalid condition operator")
        res = self.__conn.cursor().execute(f"SELECT file.fsid, file.inode, file.path, file.id, r.value FROM (\
                                            SELECT rel_file_tag_int.tag_id, rel_file_tag_int.file_id, rel_file_tag_int.value \
                                            FROM rel_file_tag_int LEFT JOIN tag ON rel_file_tag_int.tag_id == tag.id\
                                            WHERE tag.id == ?) AS r\
                                            LEFT JOIN file ON r.file_id == file.id \
                                            WHERE r.value {operator} ?", (self.__get_tag_id(tag_name), condition))
        return {(x[0], x[1], x[2], x[3], ":".join([tag_name, str(x[4])])) for x in res.fetchall()}
    
    def _direct_rels_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int, str]]:
        """Return direct relationships for tag.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Tuples containing (fsid, inode, filepath, file entry id, tag name (+ value)).
        """

        tag_type = self.get_tag_type(tag_name)
        match tag_type:
            case "str":
                return self._direct_str_rels_for_tag(tag_name)
            case "int":
                return self._direct_int_rels_for_tag(tag_name)
        return self._direct_null_rels_for_tag(tag_name)

    def _direct_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        """Return file data of direct relationships for tag.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of tuple of (int, int, str, int)
            Tuples containing (fsid, inode, filepath, file entry id).
        """

        return {x[0:4] for x in self._direct_rels_for_tag(tag_name)}

    
    def _direct_inferiors_for_tag(self, tag_name : str) -> set[str]:
        """Return direct tag-subtag relationships where given tag is the superior.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of str
            Set of inferior tag names.
        """

        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.superior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.inferior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    def _direct_superiors_for_tag(self, tag_name : str) -> set[str]:
        """Return direct tag-subtag relationships where given tag is the inferior.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of str
            Set of superior tag names.
        """
        
        res = self.__conn.cursor().execute("SELECT tag.name FROM (\
                                        SELECT rel_tag_tag.superior_id, rel_tag_tag.inferior_id \
                                        FROM rel_tag_tag LEFT JOIN tag ON rel_tag_tag.inferior_id == tag.id\
                                        WHERE tag.id == ?) AS r\
                                    LEFT JOIN tag ON r.superior_id == tag.id", (self.__get_tag_id(tag_name),))
        return {x[0] for x in res.fetchall()}

    # query functions
    
    def get_tags(self) -> set[str]:
        """Return set of all tag entry names.
        
        Returns
        ----------
        set of str
        """

        res = self.__conn.cursor().execute ("SELECT name FROM tag")
        return set([x[0] for x in res.fetchall()])
    
    def get_files(self) -> set[tuple[int, int]]:
        """Return (fsid, inode) pairs for all file entries.
        
        Returns
        ----------
        set of tuple of (int, int)
        """
        
        res = self.__conn.cursor().execute ("SELECT fsid, inode, path FROM file")
        return set([(x[0], x[1]) for x in res.fetchall()])
    
    def get_complete_file_entries(self) -> set[tuple[int, int, str, int]]:
        """Return (fsid, inode, path, database id) tuples for all file entries.
        
        Returns
        ----------
        set of tuple of (int, int, str, int)
        """

        res = self.__conn.cursor().execute ("SELECT fsid, inode, path, id FROM file")
        return set([(x[0], x[1], x[2], x[3]) for x in res.fetchall()])
    
    def get_rels_for_file(self, fsid : int, inode : int) -> dict[str, str | int | None]:
        """Return direct and inherited file-tag relationships for file.
        
        Parameters
        ----------
        fsid : int
        inode : int

        Returns
        -------
        dict of {str : str, int or None}
            Dictionary in format (tag_name : value).
        """
        
        output = {}
        direct_rels = self._direct_rels_for_file(fsid, inode)
        output.update(direct_rels)
        for tag_name in direct_rels.keys():
            output.update({superior : None for superior in self.get_superiors_tree(tag_name)})
        return output

    def get_tags_for_file(self, fsid : int, inode : int) -> set[str]:
        """Return tag names of direct and inherited file-tag relationships for file.
        
        Parameters
        ----------
        fsid : int
        inode : int

        Returns
        -------
        set of str
        """

        output = set()
        direct_tags = self._direct_tags_for_file(fsid, inode)
        output.update(direct_tags)
        for tag_name in direct_tags:
            output.update(self.get_superiors_tree(tag_name))
        return output
    
    def get_rels_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int, str]]:
        """Return direct and inherited file-tag relationships for tag.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of tuple of (int, int, str, int, str)
            Tuples in format (fsid, inode, path, file id, tag_name + value).
        """

        output = set()
        direct_rels = self._direct_rels_for_tag(tag_name)
        output.update(direct_rels)
        for rel in self.get_inferiors_tree(tag_name):
            output.update(self._direct_rels_for_tag(rel))
        return output
    
    def get_files_for_tag(self, tag_name : str) -> set[tuple[int, int, str, int]]:
        """Return file data of direct and inherited file-tag relationships for tag.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of tuple of (int, int, str, int)
            Tuples in format (fsid, inode, path, file id).
        """
        
        output = self._direct_files_for_tag(tag_name)
        for rel in self.get_inferiors_tree(tag_name):
            output.update(self._direct_files_for_tag(rel))
        return output

    def get_tag_type(self, tag_name : str) -> str:
        """Return internal string representation of tag's data type.
        
        Parameters
        ----------
        tag_name : str

        Returns
        -------
        str
        """

        res = self.__conn.cursor().execute("SELECT type FROM tag WHERE name == ?", (tag_name,))
        return res.fetchone()[0]

    def get_root_tags(self) -> set[str]:
        """Return set of all tags which have no superiors.
        
        Returns
        -------
        set of str
        """

        res = self.__conn.cursor().execute(
            "SELECT tag.name \
            FROM tag LEFT JOIN rel_tag_tag ON tag.id = rel_tag_tag.inferior_id \
            WHERE rel_tag_tag.inferior_id IS NULL"
        )
        return set([x[0] for x in res.fetchall()])
    
    def get_inferiors_tree(self, tag_name : str) -> set[str]:
        """Return set of all direct and indirect subtags for tag.

        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of str
        """

        output = set()
        queue = [tag_name]
        while queue:
            current = queue.pop()
            res = self._direct_inferiors_for_tag(current)
            queue.extend(res)
            output.update(res)
        return output

    def get_superiors_tree(self, tag_name : str) -> set[str]:
        """Return set of all direct and indirect superior tags for tag.

        Parameters
        ----------
        tag_name : str

        Returns
        -------
        set of str
        """

        output = set()
        queue = [tag_name]
        while queue:
            current = queue.pop()
            res = self._direct_superiors_for_tag(current)
            queue.extend(res)
            output.update(res)
        return output
    

    # file management
    
    def set_file_path(self, fsid : int, inode : int, filepath : str):
        """Set given filepath to file entry identified by (fsid, inode).

        Parameters
        ----------
        fsid : int
        inode : int
        filepath : str
        """

        self.__conn.cursor().execute("UPDATE file SET path = ? WHERE fsid == ? AND inode == ?", (filepath, fsid, inode))
        self.__conn.commit()

    def set_file_fsid_inode(self, fsid : int, inode : int, filepath : str):
        """Set (fsid, inode) to file entry identified by filepath.
        
        Parameters
        ----------
        fsid : int
        inode : int
        filepath : str
        """
        
        self.__conn.cursor().execute("UPDATE file SET fsid = ?, inode = ? WHERE path == ?", (fsid, inode, filepath))
        self.__conn.commit()

    def get_file_by_path(self, path: str) -> tuple[int, int, str, int] | None:
        """Return file entry identified by path.
        
        Parameters
        ----------
        filepath : str

        Returns
        -------
        tuple of (int, int, str, int) or None
            Tuple in format (fsid, inode, path, database id).
        """

        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path == ?", (path,))
        try:
            return res.fetchall()[0]
        except IndexError:
            return None

    def get_file_by_fsid_inode(self, fsid : int, inode: int) -> tuple[int, int, str, int] | None:
        """Return file entry identified by (fsid, inode).
        
        Parameters
        ----------
        fsid : int
        inode : int

        Returns
        -------
        tuple of (int, int, str, int) or None
            Tuple in format (fsid, inode, path, database id).
        """

        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE fsid == ? AND inode == ?", (fsid, inode))
        try:
            return res.fetchall()[0]
        except IndexError:
            return None
        
    def get_file_by_id(self, entry_id : int) -> tuple[int, int, str, int] | None:
        """Return file entry identified by database id.
        
        Parameters
        ----------
        entry_id : int

        Returns
        -------
        tuple of (int, int, str, int) or None
            Tuple in format (fsid, inode, path, database id).
        """
        
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE id == ?", (entry_id,))
        try:
            return res.fetchall()[0]
        except IndexError:
            return None
        
    def get_files_by_path_prefix(self, path_prefix: str) -> list[tuple[int, int, str, int]]:
        """Return file entries whose paths start with provided prefix.
        
        Parameters
        ----------
        path_prefix : str

        Returns
        -------
        list of tuple of (int, int, str, int)
            Tuples in format (fsid, inode, path, database id).
        """
        
        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path LIKE ?", (path_prefix + '%',))
        return res.fetchall()
    
    def get_files_by_path_suffix(self, path_suffix: str) -> list[tuple[int, int, str, int]]:
        """Return file entries whose paths end with provided suffix.
        
        Parameters
        ----------
        path_suffix : str

        Returns
        -------
        list of tuple of (int, int, str, int)
            Tuples in format (fsid, inode, path, database id).
        """

        res = self.__conn.cursor().execute("SELECT fsid, inode, path, id FROM file WHERE path LIKE ?", ('%' + path_suffix,))
        return res.fetchall()
    
        
    def is_known_and_is_awake_fs(self, fsid : int) -> bool | None:
        """Resolve if an entry exists for provided fsid and is marked currently active in database.

        Parameters
        ----------
        fsid : int

        Returns
        -------
        bool or None
            None if entry doesn't exist, True if FS entry is marked awake, False if FS entry is marked sleeping.
        """
        
        res = self.__conn.cursor().execute("SELECT active FROM filesystem WHERE fsid == ?", (fsid,))
        try:
            return res.fetchone()[0]
        except TypeError:
            return 
        
    def set_fs_active(self, fsid : int, active : bool = True):
        """Mark FS entry as active (or inactive).
        
        Parameters
        ----------
        fsid : int
        active : bool, default=True
        """

        self.__conn.cursor().execute("INSERT OR IGNORE INTO filesystem VALUES (NULL, ?, ?)", (fsid, active))
        self.__conn.cursor().execute("UPDATE filesystem SET active = ? WHERE fsid == ?", (active, fsid))
        self.__conn.commit()
        
    def set_fs_sleep(self, fsid : int):
        """Mark FS entry as asleep.
        
        Parameters
        ----------
        fsid : int
        """

        self.set_fs_active(fsid, False)
    