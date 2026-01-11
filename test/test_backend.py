import unittest
import backend
import settings
import database as db , errors as e


testDB = db.Database("test/data/testDB.db")
filepath = "test/data/fake_file_system/empty.txt"

class TestCommandBackend(unittest.TestCase):

    def test_tag_untag(self):
        backend.command_TAG(filepath, "tag1")
        backend.command_TAG(filepath, "tag2")

        table = testDB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "tag1"), (2, "tag2")])
        self.assertEqual(len(table['file']), 1)
        self.assertEqual(table['file'][0][0], 1)
        self.assertListEqual(table['rel_tag_file'], [(1, 1, 1), (2, 1, 2)])

        backend.command_UNTAG(filepath, "tag1")

        table = testDB.dump_tables()
        self.assertListEqual(table['tag'], [(2, "tag2")])
        self.assertEqual(len(table['file']), 1)
        self.assertListEqual(table['rel_tag_file'], [(2, 1, 2)])

        backend.command_UNTAG(filepath, "tag2")
        
        table = testDB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_tag_file'], [])

    def test_errors(self):
        pass

    def test_listings(self):
        backend.command_TAG(filepath, "tag1")
        backend.command_TAG(filepath, "tag2")

        self.assertListEqual(["tag1", "tag2"], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual(["tag1", "tag2"], backend.command_LIST_EXISTING_TAGS())

        backend.command_DEL_TAG("tag1")

        self.assertListEqual(["tag2"], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual(["tag2"], backend.command_LIST_EXISTING_TAGS())

        backend.command_DEL_TAG("tag2")

        self.assertListEqual([], backend.command_LIST_TAGS_FOR_FILE(filepath))
        self.assertListEqual([], backend.command_LIST_EXISTING_TAGS())

if __name__ == '__main__':
    settings.testing = True
    settings.backup_path = settings.database_path
    settings.database_path = settings.test_database_path
    unittest.main()
    settings.testing = False
    settings.database_path = settings.backup_path