import unittest
import os
from semo import database as db 

class TestDatabaseCommands(unittest.TestCase):
    def setUp(self):
        self.path = "test/data/testDB.db"
        self.testDB = db.Database(self.path)
        self.testDB.init_create_script()
        self.file_system = 0
    def tearDown(self):
        os.remove(self.path)
        
    def test_verify_empty_db(self):
        con = db.sql.connect("test/data/emptyDB.db")
        cur = con.cursor()
        empty_db = db.Database("test/data/emptyDB.db")
        self.assertTrue(empty_db.verify_db())
        os.remove("test/data/emptyDB.db")

    def test_verify_correct_db(self):
        con = db.sql.connect("test/data/correctDB.db")
        db_init = db.Database("test/data/correctDB.db")
        db_init.init_create_script()

        correct_db = db.Database("test/data/correctDB.db")
        self.assertTrue(correct_db.verify_db())
        os.remove("test/data/correctDB.db")

    def test_verify_incorrect_db(self):
        con = db.sql.connect("test/data/incorrectDB.db")
        cur = con.cursor()
        cur.execute("PRAGMA foreign_keys = ON")
        cur.execute("CREATE TABLE IF NOT EXISTS tag(\
                              id INTEGER PRIMARY KEY, \
                              name VARCHAR(50) NOT NULL UNIQUE\
                              )")
        con.commit()
        incorrect_db = db.Database("test/data/incorrectDB.db")
        self.assertFalse(incorrect_db.verify_db())
        os.remove("test/data/incorrectDB.db")

    def test_dump_tables(self):
        pattern = {'tag' : [], 'file' : [], 'rel_file_tag' : [], 'rel_tag_tag' : []}
        self.assertDictEqual(pattern, self.testDB.dump_tables())

    def test_new_tag(self):
        tag_name = 'test_new_tag'
        self.testDB.new_tag(tag_name)
        self.assertTrue((1, tag_name) in self.testDB.dump_tables()['tag'])
        self.testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name) in self.testDB.dump_tables()['tag'])

    def test_new_tag_duplicate(self):
        tag_name = 'test_new_tag_duplicate'
        self.testDB.new_tag(tag_name)
        with self.assertRaises(Exception):
            self.testDB.new_tag(tag_name)
        self.testDB.delete_tag(tag_name)

    def test_delete_nonexistent_tag(self):
        tag_name = 'test_delete_nonexistent_tag'
        with self.assertRaises(Exception):
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
        with self.assertRaises(Exception):
            self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.delete_file(self.file_system, inode)

    def test_delete_nonexistent_file(self):
        inode = 1
        filename = 'test_delete_nonexistent_file'
        with self.assertRaises(Exception):
            self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag(self):
        inode = 1
        filename = 'test_new_rel_file_tag_f'
        tag_name = 'test_new_rel_file_tag_t'

        self.assertTrue(self.testDB.dump_tables()['tag'] == [])
        self.testDB.new_tag(tag_name)
        self.assertListEqual([(1, tag_name)], self.testDB.dump_tables()['tag'])

        self.testDB.new_file(self.file_system, inode, filename)
        tables = self.testDB.dump_tables()
        self.assertTrue((1, tag_name) in tables['tag'])
        self.assertTrue((1, self.file_system, inode, filename) in tables['file'])

        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)
        self.assertTrue((1, 1, 1) in self.testDB.dump_tables()['rel_file_tag'])
        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.assertFalse((1, 1, 1) in self.testDB.dump_tables()['rel_file_tag'])

        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_duplicate(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_duplicate'
        filename = 'test_new_rel_file_tag_duplicate_f'

        self.testDB.new_tag(tag_name)
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        with self.assertRaises(Exception):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

    def test_new_rel_file_tag_nonexistent(self):
        inode = 1
        tag_name = 'test_new_rel_file_tag_nonexistent'
        filename = 'test_new_rel_file_tag_nonexistent_f'

        with self.assertRaises(Exception):
            self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        self.testDB.new_tag(tag_name)
        with self.assertRaises(Exception):
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

        self.assertListEqual([(1, tag1_name), (2, tag2_name)], self.testDB.dump_tables()['tag'])

        self.testDB.new_rel_tag_tag(tag1_name, tag2_name)
        self.assertTrue((1, 1, 2) in self.testDB.dump_tables()['rel_tag_tag'])
        self.testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.assertFalse((1, 1, 2) in self.testDB.dump_tables()['rel_file_tag'])

        self.testDB.delete_tag(tag1_name)
        self.testDB.delete_tag(tag2_name)

    def test_new_rel_tag_tag_duplicate(self):
        tag1_name = 'test_new_rel_tag_tag_duplicate1'
        tag2_name = 'test_new_rel_tag_tag_duplicate2'

        self.testDB.new_tag(tag1_name)
        self.testDB.new_tag(tag2_name)

        self.testDB.new_rel_tag_tag(tag1_name, tag2_name)
        with self.assertRaises(Exception):
            self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.testDB.delete_tag(tag1_name)
        self.testDB.delete_tag(tag2_name)

    def test_new_rel_tag_tag_nonexistent(self):
        tag1_name = 'test_new_rel_tag_tag_nonexistent1'
        tag2_name = 'test_new_rel_tag_tag_nonexistent2'

        with self.assertRaises(Exception):
            self.testDB.new_rel_tag_tag(tag1_name, tag2_name)

        self.testDB.new_tag(tag1_name)
        with self.assertRaises(Exception):
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

    def test_list_files_for_tag(self):
        inode = 1
        filename = 'test_list_files_for_tag_f'
        tag_name = 'test_list_files_for_tag'

        self.testDB.new_tag(tag_name)
        self.testDB.new_file(self.file_system, inode, filename)
        self.testDB.new_rel_file_tag(self.file_system, inode, tag_name)

        table = self.testDB.dump_tables()
        self.assertSetEqual({(self.file_system, inode, filename)}, self.testDB.get_files_for_tag(tag_name))

        self.testDB.delete_rel_file_tag(self.file_system, inode, tag_name)
        self.testDB.delete_tag(tag_name)
        self.testDB.delete_file(self.file_system, inode)

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