import unittest

from semo import backend
from semo import database as db

testDB2 = db.Database("test/data/testDB.db")
testDB2.init_create_script()
filepath = "test/data/fake_file_system/empty.txt"

class TestCommandBackend(unittest.TestCase):
    def test_tag_untag(self):
        backend.command_TAG(filepath, "tag1")
        backend.command_TAG(filepath, "tag2")

        table = testDB2.dump_tables()
        self.assertListEqual(table['tag'], [(1, "tag1"), (2, "tag2")])
        self.assertEqual(len(table['file']), 1)
        self.assertEqual(table['file'][0][0], 1)
        self.assertListEqual(table['rel_file_tag'], [(1, 1, 1), (2, 1, 2)])

        backend.command_UNTAG(filepath, "tag1")

        table = testDB2.dump_tables()
        self.assertListEqual(table['tag'], [(2, "tag2")])
        self.assertEqual(len(table['file']), 1)
        self.assertListEqual(table['rel_file_tag'], [(2, 1, 2)])

        backend.command_UNTAG(filepath, "tag2")
        
        table = testDB2.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag'], [])

    def test_listings(self):
        backend.command_TAG(filepath, "tag1")
        backend.command_TAG(filepath, "tag2")

        self.assertListEqual([(1, "tag1"), (2, "tag2")], testDB2.dump_tables()['tag'])
        self.assertListEqual(["tag1", "tag2"], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual(["tag1", "tag2"], backend.command_LIST_EXISTING_TAGS())

        backend.command_DEL_TAG("tag1")

        self.assertListEqual([(2,"tag2")], testDB2.dump_tables()['tag'])
        self.assertEqual(len(testDB2.dump_tables()['file']), 1)
        self.assertListEqual([(2, 1, 2)], testDB2.dump_tables()['rel_file_tag'])    

        self.assertListEqual(["tag2"], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual(["tag2"], backend.command_LIST_EXISTING_TAGS())

        backend.command_DEL_TAG("tag2")

        self.assertListEqual([], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual([], backend.command_LIST_EXISTING_TAGS())


if __name__ == '__main__':
    unittest.main()