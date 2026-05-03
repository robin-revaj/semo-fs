import unittest
import os
import database as db, utils
from utils import SemoException

class TestDatabaseCommands(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.path = utils.get_test_db()
        utils.set_working_db(cls.path)
        cls.testDB = db.Database(cls.path)
        cls.file_system = 0
        return super().setUpClass()
    @classmethod
    def tearDownClass(cls) -> None:
        utils.set_working_db(utils.get_default_db())
        os.remove(cls.path)
        return super().tearDownClass()
    def tearDown(self):
        self.testDB.clear_contents()
        
    def test_verify_empty_db(self):
        con = db.sql.connect("tests/data/emptyDB.db")
        empty_db = db.Database("tests/data/emptyDB.db")
        self.assertTrue(empty_db.verify_db())
        os.remove("tests/data/emptyDB.db")

    def test_verify_correct_db(self):
        con = db.sql.connect("tests/data/correctDB.db")
        db_init = db.Database("tests/data/correctDB.db")
        #db_init.init_create_script()

        correct_db = db.Database("tests/data/correctDB.db")
        self.assertTrue(correct_db.verify_db())
        os.remove("tests/data/correctDB.db")

    def test_verify_incorrect_db(self):
        con = db.sql.connect("tests/data/incorrectDB.db")
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("CREATE TABLE IF NOT EXISTS tag(\
                              id INTEGER PRIMARY KEY, \
                              name VARCHAR(50) NOT NULL UNIQUE\
                              )")
        con.commit()
        with self.assertRaises(SemoException):
            incorrect_db = db.Database("tests/data/incorrectDB.db")
        os.remove("tests/data/incorrectDB.db")

    def test_dump_tables(self):
        pattern = {'tag' : [], 'file' : [], 'rel_file_tag_null' : [], 'rel_file_tag_str' : [], 'rel_file_tag_int' : [], 'rel_tag_tag' : []}
        self.assertDictEqual(pattern, self.testDB.dump_tables())

    def test_new_tag(self):
        tag_name = 'test_new_tag'
        self.testDB.new_tag(tag_name, None)
        self.assertTrue((1, tag_name, None) in self.testDB.dump_tables()['tag'])
        self.testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name, None) in self.testDB.dump_tables()['tag'])

    def test_new_tag_typed(self):
        tag_name = 'test_new_tag_typed'
        self.testDB.new_tag(tag_name, "str")
        self.assertTrue((1, tag_name, "str") in self.testDB.dump_tables()['tag'])
        self.testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name, "str") in self.testDB.dump_tables()['tag'])

    def test_new_tag_duplicate(self):
        tag_name = 'test_new_tag_duplicate'
        self.testDB.new_tag(tag_name)
        with self.assertRaises(SemoException):
            self.testDB.new_tag(tag_name)
        self.testDB.delete_tag(tag_name)

    def test_delete_nonexistent_tag(self):
        tag_name = 'test_delete_nonexistent_tag'
        with self.assertRaises(SemoException):
            self.testDB.delete_tag(tag_name)

    def test_new_file(self):
        inode = 1
        filename = 'test_new_file'
        self.testDB.new_file(self.file_system, inode, filename)
        self.assertTrue((1, self.file_system, inode, filename) in self.testDB.dump_tables()['file'])
        self.testDB.delete_file(self.file_system, inode)
        self.assertFalse((1, self.file_system, inode, filename) in self.testDB.dump_tables()['file'])

    def test_new_file_duplicate(self):
        inode = 1
        filename = 'test_new_file_duplicate'
        self.testDB.new_file(self.file_system, inode, filename)
        with self.assertRaises(SemoException):
            self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.delete_file(self.file_system, inode)

    def test_delete_nonexistent_file(self):
        inode = 1
        filename = 'test_delete_nonexistent_file'
        with self.assertRaises(SemoException):
            self.testDB.delete_file(self.file_system, inode)

    def test_new_null_rel_file_tag(self):
        inode = 1
        filename = 'test_new_null_rel_file_tag_f'
        tag_name = 'test_new_null_rel_file_tag_t'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(tag_name)
        self.assertListEqual([(1, tag_name, None)], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)
        tables = self.testDB.dump_tables()
        self.assertTrue((1, self.file_system, inode, filename) in tables['file'])

        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)
        self.assertTrue((1, 1, 1) in self.testDB.dump_tables()['rel_file_tag_null'])
        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.assertFalse((1, 1, 1) in self.testDB.dump_tables()['rel_file_tag_null'])

        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_str_rel_file_tag(self):
        inode = 1
        filename = 'test_new_str_rel_file_tag_f'
        tag_name = 'test_new_str_rel_file_tag_t'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(tag_name, "str")
        self.assertListEqual([(1, tag_name, "str")], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)
        tables = self.testDB.dump_tables()
        self.assertTrue((1, self.file_system, inode, filename) in tables['file'])

        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name, "stringvalue")
        self.assertTrue((1, 1, 1, "stringvalue") in self.testDB.dump_tables()['rel_file_tag_str'])
        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.assertFalse((1, 1, 1, "stringvalue") in self.testDB.dump_tables()['rel_file_tag_str'])

        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_int_rel_file_tag(self):
        inode = 1
        filename = 'test_new_int_rel_file_tag_f'
        tag_name = 'test_new_int_rel_file_tag_t'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(tag_name, "int")
        self.assertListEqual([(1, tag_name, "int")], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)
        tables = self.testDB.dump_tables()
        self.assertTrue((1, self.file_system, inode, filename) in tables['file'])

        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name, 2)
        self.assertTrue((1, 1, 1, 2) in self.testDB.dump_tables()['rel_file_tag_int'])
        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.assertFalse((1, 1, 1, 2) in self.testDB.dump_tables()['rel_file_tag_int'])

        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag(self):
        inode = 1
        filename = 'test_new_rel_file_tag_f'
        nulltag = 'test_new_rel_file_tag_nulltag'
        strtag = 'test_new_rel_file_tag_strtag'
        inttag = 'test_new_rel_file_tag_inttag'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(nulltag)
        self.testDB.new_tag(strtag, "str")
        self.testDB.new_tag(inttag, "int")
        self.assertListEqual([(1, nulltag, None), (2, strtag, "str"), (3, inttag, "int")], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)

        self.testDB.new_rel_file_tag(self.file_system, inode, nulltag)
        self.testDB.new_rel_file_tag(self.file_system, inode, strtag, "string")
        self.testDB.new_rel_file_tag(self.file_system, inode, inttag, 42)
        tables = self.testDB.dump_tables()
        self.assertTrue((1, 1, 1) in tables['rel_file_tag_null'])
        self.assertTrue((1, 1, 2, "string") in tables['rel_file_tag_str'])
        self.assertTrue((1, 1, 3, 42) in tables['rel_file_tag_int'])
        self.testDB.delete_rel_file_tag(self.file_system, inode, nulltag)
        self.testDB.delete_rel_file_tag(self.file_system, inode, strtag)
        self.testDB.delete_rel_file_tag(self.file_system, inode, inttag)
        tables = self.testDB.dump_tables()
        self.assertListEqual([], tables['rel_file_tag_null'])
        self.assertListEqual([], tables['rel_file_tag_str'])
        self.assertListEqual([], tables['rel_file_tag_int'])
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_wrong_value_type(self):
        inode = 1
        filename = 'test_new_rel_file_tag_f'
        nulltag = 'test_new_rel_file_tag_nulltag'
        strtag = 'test_new_rel_file_tag_strtag'
        inttag = 'test_new_rel_file_tag_inttag'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(nulltag)
        self.testDB.new_tag(strtag, "str")
        self.testDB.new_tag(inttag, "int")
        self.assertListEqual([(1, nulltag, None), (2, strtag, "str"), (3, inttag, "int")], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)

        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, nulltag, "string")
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, nulltag, 42)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, strtag)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, strtag, 42)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, inttag)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, inttag, "string")
        tables = self.testDB.dump_tables()
        self.assertTrue(tables['rel_file_tag_null'] == [])
        self.assertTrue(tables['rel_file_tag_str'] == [])
        self.assertTrue(tables['rel_file_tag_int'] == [])
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_null_duplicate(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_null_duplicate'
        filename = 'test_new_rel_file_tag_null_duplicate_f'

        self.testDB.new_tag(tag_name)
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_str_duplicate(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_str_duplicate'
        filename = 'test_new_rel_file_tag_str_duplicate_f'

        self.testDB.new_tag(tag_name, "s42")
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_int_duplicate(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_int_duplicate'
        filename = 'test_new_rel_file_tag_int_duplicate_f'

        self.testDB.new_tag(tag_name, 42)
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_nonexistent(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_nonexistent'
        filename = 'test_new_rel_file_tag_nonexistent_f'

        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.new_tag(tag_name)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_tag_tag(self):
        tag1_name = 'test_new_rel_tag_tag1'
        tag2_name = 'test_new_rel_tag_tag2'

        self.testDB.new_tag(tag1_name)
        self.testDB.new_tag(tag2_name)

        self.assertListEqual([(1, tag1_name, None), (2, tag2_name, None)], self.testDB.dump_tables()['tag'])

        self.testDB.new_rel_tag_tag(tag1_name, tag2_name)
        self.assertTrue((1, 1, 2) in self.testDB.dump_tables()['rel_tag_tag'])
        self.testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.assertFalse((1, 1, 2) in self.testDB.dump_tables()['rel_tag_tag'])

        self.testDB.delete_tag(tag1_name)
        self.testDB.delete_tag(tag2_name)

    def test_new_rel_tag_tag_duplicate(self):
        tag1_name = 'test_new_rel_tag_tag_duplicate1'
        tag2_name = 'test_new_rel_tag_tag_duplicate2'

        self.testDB.new_tag(tag1_name)
        self.testDB.new_tag(tag2_name)

        self.testDB.new_rel_tag_tag(tag1_name, tag2_name)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.testDB.delete_tag(tag1_name)
        self.testDB.delete_tag(tag2_name)

    def test_new_rel_tag_tag_nonexistent(self):
        tag1_name = 'test_new_rel_tag_tag_nonexistent1'
        tag2_name = 'test_new_rel_tag_tag_nonexistent2'

        with self.assertRaises(SemoException):
            self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.new_tag(tag1_name)
        with self.assertRaises(SemoException):
            self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.new_tag(tag2_name)
        self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.testDB.delete_tag(tag1_name)
        self.testDB.delete_tag(tag2_name)

    def test_list_tags(self):
        tag_name = 'test_list_tags'
        self.testDB.new_tag(tag_name)
        self.assertSetEqual({tag_name}, self.testDB.get_tags())
        self.testDB.delete_tag(tag_name)

    def test_list_files(self):
        inode = 1
        filename = 'test_list_files'
        self.testDB.new_file(self.file_system, inode, filename)
        self.assertSetEqual({(self.file_system, inode)}, self.testDB.get_files())
        self.testDB.delete_file(self.file_system, inode)

    def test_list_tags_for_file(self):
        inode = 1
        filename = 'test_list_tags_for_file_f'
        tag_name = 'test_list_tags_for_file'

        self.testDB.new_tag(tag_name)
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.assertSetEqual({tag_name}, self.testDB.get_tags_for_file(self.file_system, inode))

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_list_rels_for_file(self):
        inode = 1
        filename = 'test_list_tags_for_file_f'
        nulltag = 'test_list_tags_for_file_null'
        inttag = 'test_list_tags_for_file_int'
        strtag = 'test_list_tags_for_file_str'

        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_tag(nulltag)
        self.testDB.new_rel_file_tag(self.file_system, inode, nulltag)
        self.testDB.new_tag(strtag, "str")
        self.testDB.new_rel_file_tag(self.file_system, inode, strtag, "s42")
        self.testDB.new_tag(inttag, "int")
        self.testDB.new_rel_file_tag(self.file_system, inode, inttag, 42)

        self.assertDictEqual({nulltag:None, strtag:"s42", inttag:42}, self.testDB.get_rels_for_file(self.file_system, inode))

        self.testDB.delete_rel_file_tag(self.file_system, inode, nulltag)
        self.testDB.delete_rel_file_tag(self.file_system, inode, strtag)
        self.testDB.delete_rel_file_tag(self.file_system, inode, inttag)
        self.assertDictEqual({}, self.testDB.get_rels_for_file(self.file_system, inode))

    def test_list_files_for_tag(self):
        inode = 1
        filename = 'test_list_files_for_tag_f'
        nulltag = 'test_list_files_for_tag_null'
        inttag = 'test_list_files_for_tag_int'
        strtag = 'test_list_files_for_tag_str'

        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_tag(nulltag)
        self.testDB.new_rel_file_tag(self.file_system, inode, nulltag)
        self.testDB.new_tag(strtag, "str")
        self.testDB.new_rel_file_tag(self.file_system, inode, strtag, "s42")
        self.testDB.new_tag(inttag, "int")
        self.testDB.new_rel_file_tag(self.file_system, inode, inttag, 42)

        self.assertSetEqual({(self.file_system, inode, filename, 1)}, self.testDB.get_files_for_tag(nulltag))
        self.assertSetEqual({(self.file_system, inode, filename, 1)}, self.testDB.get_files_for_tag(strtag))
        self.assertSetEqual({(self.file_system, inode, filename, 1)}, self.testDB.get_files_for_tag(inttag))

        self.assertSetEqual({(self.file_system, inode, filename, 1, None)}, self.testDB.get_rels_for_tag(nulltag))
        self.assertSetEqual({(self.file_system, inode, filename, 1, "s42")}, self.testDB.get_rels_for_tag(strtag))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB.get_rels_for_tag(inttag))

    def test_list_subtags_for_tag(self):
        root_name = 'test_list_subtags_for_tag_root'
        subtag_name = 'test_list_subtags_for_tag_subtag'

        self.testDB.new_tag(root_name)
        self.testDB.new_tag(subtag_name)
        self.testDB.new_rel_tag_tag(root_name, subtag_name)

        self.assertSetEqual({subtag_name}, self.testDB._direct_inferiors_for_tag(root_name))

        self.testDB.delete_rel_tag_tag(root_name, subtag_name)
        self.testDB.delete_tag(root_name)
        self.testDB.delete_tag(subtag_name)

    def test_list_superior_tags_for_tag(self):
        root_name = 'test_list_superior_tags_for_tag_root'
        subtag_name = 'test_list_superior_tags_for_tag_subtag'

        self.testDB.new_tag(root_name)
        self.testDB.new_tag(subtag_name)
        self.testDB.new_rel_tag_tag(root_name, subtag_name)

        self.assertSetEqual({root_name}, self.testDB._direct_superiors_for_tag(subtag_name))

        self.testDB.delete_rel_tag_tag(root_name, subtag_name)
        self.testDB.delete_tag(root_name)
        self.testDB.delete_tag(subtag_name)

    def test_list_root_tags(self):
        root1_name = 'test_list_root_tags_root1'
        root2_name = 'test_list_root_tags_root2'
        subtag_name = 'test_list_root_tags_subtag'

        self.testDB.new_tag(root1_name)
        self.testDB.new_tag(root2_name)
        self.testDB.new_tag(subtag_name)
        self.testDB.new_rel_tag_tag(root1_name, subtag_name)
        self.testDB.new_rel_tag_tag(root2_name, subtag_name)

        self.assertSetEqual({root1_name, root2_name}, self.testDB.get_root_tags())

        self.testDB.delete_rel_tag_tag(root1_name, subtag_name)
        self.testDB.delete_rel_tag_tag(root2_name, subtag_name)
        self.testDB.delete_tag(root1_name)
        self.testDB.delete_tag(root2_name)
        self.testDB.delete_tag(subtag_name)

    def test_list_inferiors_tree(self):
        names = ["t1", "t2", "t3", "t4", "t5"]
        for i in range(5):
            self.testDB.new_tag(names[i])
        self.testDB.new_rel_tag_tag("t1", "t2")
        self.testDB.new_rel_tag_tag("t2", "t3")
        self.testDB.new_rel_tag_tag("t3", "t4")
        self.testDB.new_rel_tag_tag("t4", "t5")
        self.assertSetEqual(set(names[1:]), self.testDB.get_inferiors_tree("t1"))
        self.assertSetEqual(set(), self.testDB.get_inferiors_tree("t5"))
        self.testDB.clear_contents()

    def test_list_superiors_tree(self):
        names = ["t1", "t2", "t3", "t4", "t5"]
        for i in range(5):
            self.testDB.new_tag(names[i])
        self.testDB.new_rel_tag_tag("t1", "t2")
        self.testDB.new_rel_tag_tag("t2", "t3")
        self.testDB.new_rel_tag_tag("t3", "t4")
        self.testDB.new_rel_tag_tag("t4", "t5")
        self.assertSetEqual(set(names[:4]), self.testDB.get_superiors_tree("t5"))
        self.assertSetEqual(set(), self.testDB.get_superiors_tree("t1"))
        self.testDB.clear_contents()

    def test_str_rels_with_equals_condition(self):
        tagname = "test_str_rels_with_condition"
        inode = 1
        filename = "filename"
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_tag(tagname, "str")
        self.testDB.new_rel_file_tag(self.file_system, inode, tagname, "s42")
        self.assertTrue((1, 1, 1, "s42") in self.testDB.dump_tables()['rel_file_tag_str'])
        self.assertDictEqual({tagname:"s42"}, self.testDB.get_rels_for_file(self.file_system, inode))
        self.assertSetEqual({(self.file_system, inode, filename, 1, "s42")}, self.testDB._str_rels_for_tag_condition(tagname, "s42"))
        self.assertSetEqual(set(), self.testDB._str_rels_for_tag_condition(tagname, "s43"))

    def test_int_rels_with_equals_condition(self):
        tagname = "test_int_rels_with_equals_condition"
        inode = 1
        filename = "filename"
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_tag(tagname, "int")
        self.testDB.new_rel_file_tag(self.file_system, inode, tagname, 42)
        self.assertTrue((1, 1, 1, 42) in self.testDB.dump_tables()['rel_file_tag_int'])
        self.assertDictEqual({tagname:42}, self.testDB.get_rels_for_file(self.file_system, inode))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB._int_rels_for_tag_condition(tagname, "==", 42))
        self.assertSetEqual(set(), self.testDB._int_rels_for_tag_condition(tagname, "==", 43))

    def test_int_rels_with_range_condition(self):
        tagname = "test_int_rels_with_range_condition"
        inode = 1
        filename = "filename"
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_tag(tagname, "int")
        self.testDB.new_rel_file_tag(self.file_system, inode, tagname, 42)
        self.assertTrue((1, 1, 1, 42) in self.testDB.dump_tables()['rel_file_tag_int'])
        self.assertDictEqual({tagname:42}, self.testDB.get_rels_for_file(self.file_system, inode))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB._int_rels_for_tag_condition(tagname, "<", 50))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB._int_rels_for_tag_condition(tagname, ">", 5))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB._int_rels_for_tag_condition(tagname, "<=", 50))
        self.assertSetEqual({(self.file_system, inode, filename, 1, 42)}, self.testDB._int_rels_for_tag_condition(tagname, ">=", 5))
        self.assertSetEqual(set(), self.testDB._int_rels_for_tag_condition(tagname, ">", 90))
        self.assertSetEqual(set(), self.testDB._int_rels_for_tag_condition(tagname, ">=", 90))
        self.assertSetEqual(set(), self.testDB._int_rels_for_tag_condition(tagname, "<", 3))
        self.assertSetEqual(set(), self.testDB._int_rels_for_tag_condition(tagname, "<=", 3))
