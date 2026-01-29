import unittest
from semo import database as db 

testDB = db.Database("test/data/testDB.db")
testDB.init_create_script()
file_system = 0

class TestDatabaseCommands(unittest.TestCase):
    testDB = db.Database("test/data/testDB.db")
    def test_00_database_initalization(self):
        pattern = {'tag' : [], 'file' : [], 'rel_file_tag' : [], 'rel_tag_tag' : []}
        self.assertDictEqual(pattern, testDB.dump_tables())

    def test_create_delete_tag(self):
        tag_name = 'test_create_tag'

        testDB.new_tag(tag_name)
        self.assertTrue((1, tag_name) in testDB.dump_tables()['tag'])

        testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name) in testDB.dump_tables()['tag'])
    
    def test_create_delete_file(self):
        inode = 1
        testDB.new_file(file_system, inode)
        self.assertTrue((1, file_system, inode) in testDB.dump_tables()['file'])
        testDB.delete_file(file_system, inode)
        self.assertFalse((1, file_system, inode) in testDB.dump_tables()['file'])

    def test_create_delete_rel_file_tag(self):
        inode = 1
        tag_name = 'test_create_delete_rel_file_tag'

        self.assertTrue(testDB.dump_tables()['tag'] == [])
        testDB.new_tag(tag_name)
        self.assertListEqual([(1, tag_name)], testDB.dump_tables()['tag'])
        self.assertTrue((1, tag_name) in testDB.dump_tables()['tag'])

        testDB.new_file(file_system, inode)
        tables = testDB.dump_tables()
        self.assertTrue((1, tag_name) in tables['tag'])
        self.assertTrue((1, file_system, inode) in tables['file'])

        testDB.new_rel_file_tag(file_system, inode, tag_name)
        self.assertTrue((1, 1, 1) in testDB.dump_tables()['rel_file_tag'])

        testDB.delete_rel_file_tag(file_system, inode, tag_name)
        self.assertFalse((1, 1, 1) in testDB.dump_tables()['rel_file_tag'])

        testDB.new_rel_file_tag(file_system, inode, tag_name)
        testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name) in testDB.dump_tables()['tag'])
        self.assertFalse((1, 1, 1) in testDB.dump_tables()['rel_file_tag'])
        testDB.delete_file(file_system, inode)
        self.assertFalse((1, file_system, inode) in testDB.dump_tables()['file'])

    def test_create_delete_rel_tag_tag(self):
        inode = 1
        tag1_name = 'test_create_delete_rel_tag_tag1'
        tag2_name = 'test_create_delete_rel_tag_tag2'

        self.assertTrue(testDB.dump_tables()['tag'] == [])
        testDB.new_tag(tag1_name)
        testDB.new_tag(tag2_name)

        self.assertListEqual([(1, tag1_name), (2, tag2_name)], testDB.dump_tables()['tag'])

        testDB.new_rel_tag_tag(tag1_name, tag2_name)
        self.assertTrue((1, 1, 2) in testDB.dump_tables()['rel_tag_tag'])

        testDB.delete_rel_tag_tag(tag1_name, tag2_name)
        self.assertFalse((1, 1, 2) in testDB.dump_tables()['rel_file_tag'])

        testDB.new_rel_tag_tag(tag1_name, tag2_name)
        testDB.delete_tag(tag1_name)
        self.assertFalse((1, tag1_name) in testDB.dump_tables()['tag'])
        self.assertFalse((1, 1, 2) in testDB.dump_tables()['rel_tag_tag'])
        testDB.new_tag(tag1_name)
        testDB.new_rel_tag_tag(tag1_name, tag2_name)
        testDB.delete_tag(tag2_name)
        self.assertFalse((1, tag1_name) in testDB.dump_tables()['tag'])
        self.assertFalse((1, 1, 2) in testDB.dump_tables()['rel_tag_tag'])
        testDB.delete_tag(tag1_name)


    def test_list_functions_basic(self):
        inode = 1
        inode2 = 2
        tag_name = 'test_list_functions'
        tag_name2 = 'not_this_one'

        testDB.new_tag(tag_name)
        testDB.new_tag(tag_name2)
        self.assertTrue(tag_name in testDB.list_tags())
        self.assertTrue(tag_name2 in testDB.list_tags())

        testDB.new_file(file_system, inode)
        testDB.new_file(file_system, inode2)
        self.assertTrue(inode in testDB.list_files())
        self.assertTrue(inode2 in testDB.list_files())

        testDB.new_rel_file_tag(file_system, inode, tag_name)

        self.assertTrue(tag_name in testDB.list_tags_for_file(file_system, inode))
        self.assertFalse(tag_name2 in testDB.list_tags_for_file(file_system, inode))
        self.assertTrue((file_system, inode) in testDB.list_files_for_tag(tag_name))
        self.assertFalse((file_system, inode2) in testDB.list_files_for_tag(tag_name))

        testDB.delete_tag(tag_name)
        testDB.delete_tag(tag_name2)
        testDB.delete_file(file_system, inode)
        testDB.delete_file(file_system, inode2)

        self.assertListEqual([], testDB.dump_tables()['tag'])
        self.assertListEqual([], testDB.dump_tables()['file'])
        self.assertListEqual([], testDB.dump_tables()['rel_file_tag'])


    def test_list_functions_hierarchical(self):
        root1 = "root1"
        root2 = "root2"
        subtag1 = "subtag1"
        subtag2 = "subtag2"

        testDB.new_tag(root1)
        testDB.new_tag(root2)
        testDB.new_tag(subtag1)
        testDB.new_tag(subtag2)

        testDB.list_subtags_for_tag(root1)
        self.assertListEqual([], testDB.list_subtags_for_tag(root1))
        self.assertListEqual([root1, root2, subtag1, subtag2], testDB.list_root_tags())
        testDB.new_rel_tag_tag(root1, subtag1)
        self.assertListEqual([subtag1], testDB.list_subtags_for_tag(root1))
        testDB.new_rel_tag_tag(root1, subtag2)
        testDB.new_rel_tag_tag(root2, subtag2)
        self.assertListEqual([subtag1, subtag2], testDB.list_subtags_for_tag(root1))
        self.assertListEqual([subtag2], testDB.list_subtags_for_tag(root2))
        self.assertListEqual([root1, root2], testDB.list_root_tags())

        testDB.delete_tag(root1)
        testDB.delete_tag(root2)
        testDB.delete_tag(subtag1)
        testDB.delete_tag(subtag2)

        self.assertListEqual([], testDB.list_tags())
        self.assertListEqual([], testDB.dump_tables()['rel_tag_tag'])

if __name__ == '__main__':
    unittest.main()