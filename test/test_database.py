import unittest
from semo import database as db 

testDB = db.Database("test/data/testDB.db")
file_system = 0

class TestDatabaseCommands(unittest.TestCase):

    def test_00_database_initalization(self):
        pattern = {'tag' : [], 'file' : [], 'rel_tag_file' : []}
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

    def test_create_delete_rel_tag_file(self):
        inode = 1
        tag_name = 'test_create_delete_rel_tag_file'

        self.assertTrue(testDB.dump_tables()['tag'] == [])
        testDB.new_tag(tag_name)
        self.assertListEqual([(1, tag_name)], testDB.dump_tables()['tag'])
        self.assertTrue((1, tag_name) in testDB.dump_tables()['tag'])

        testDB.new_file(file_system, inode)
        tables = testDB.dump_tables()
        self.assertTrue((1, tag_name) in tables['tag'])
        self.assertTrue((1, file_system, inode) in tables['file'])

        # testDB.new_relationship(file_system, inode, tag_name)
        # self.assertTrue((1, 1, 1) in testDB.dump_tables()['rel_tag_file'])

        # testDB.delete_relationship(file_system, inode, tag_name)
        # self.assertFalse((1, 1, 1) in testDB.dump_tables()['rel_tag_file'])

        # testDB.new_relationship(file_system, inode, tag_name)
        testDB.delete_tag(tag_name)
        self.assertFalse((1, tag_name) in testDB.dump_tables()['tag'])
        self.assertFalse((1, 1, 1) in testDB.dump_tables()['rel_tag_file'])
        testDB.delete_file(file_system, inode)
        self.assertFalse((1, file_system, inode) in testDB.dump_tables()['file'])

    def test_list_functions(self):
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

        # testDB.new_relationship(file_system, inode, tag_name)

        self.assertTrue(tag_name in testDB.list_tags_for_file(file_system, inode))
        self.assertFalse(tag_name2 in testDB.list_tags_for_file(file_system, inode))
        self.assertTrue(inode in testDB.list_files_for_tag(tag_name))
        self.assertFalse(inode2 in testDB.list_files_for_tag(tag_name))

        testDB.delete_tag(tag_name)
        testDB.delete_tag(tag_name2)
        testDB.delete_file(file_system, inode)
        testDB.delete_file(file_system, inode2)

if __name__ == '__main__':
    unittest.main()