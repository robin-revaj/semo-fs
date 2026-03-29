import unittest
import os

from semo import backend
from semo import database as db


class TestCommandBackend(unittest.TestCase):
    def setUp(self):
        self.DB = db.Database("test/data/testDB.db")
        self.DB.init_create_script()
        self.loc = "test/data/"
        files = [open(self.loc + "file1.txt", "x"), open(self.loc + "file2.txt", "x"), open(self.loc + "file3.txt", "x")]
        self.files = []
        for f in files:
            self.files.append(f.name)
            f.close()
    def tearDown(self):
        os.remove("test/data/testDB.db")
        for f in self.files:
            os.remove(f)

    def test_tag_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.command_TAG(filepath, "test_tag_ok"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_ok")])
        self.assertListEqual(table['rel_file_tag'], [(1, 1, 1)])

    def test_tag_already_tagged(self):
        filepath = self.files[0]
        self.assertEqual(0, len(backend.command_TAG(filepath, "test_tag_already_tagged")))
        self.assertListEqual([f"{filepath} already tagged test_tag_already_tagged"], backend.command_TAG(filepath, "test_tag_already_tagged"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_already_tagged")])
        self.assertListEqual(table['rel_file_tag'], [(1, 1, 1)])

    def test_tag_nonexistent_file(self):
        filepath = self.loc + "nonexistent_file.txt"
        self.assertEqual(1, len(backend.command_TAG(filepath, "test_tag_nonexistent_file")))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag'], [])

    def test_tag_tagged_with_superior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.command_TAG(self.files[0], inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag']), 2)
        self.assertEqual(len(table['file']), 2)
        
        id, fs, inode, path = table['file'][0]
        self.assertSetEqual({inferior_tag}, self.DB._direct_tags_for_file(fs, inode))
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))

    def test_tag_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertEqual(1, len(backend.command_TAG(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag}, self.DB._direct_tags_for_file(fs, inode))
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))

    def test_untag_direct_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.command_TAG(filepath, "test_untag_direct_ok"))
        self.assertListEqual([], backend.command_UNTAG(filepath, "test_untag_direct_ok"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag'], [])
    
    def test_untag_indirect_ok(self):
        self.assertListEqual([], backend.command_TAG(self.files[0], "test_untag_indirect__ok1"))
        self.assertListEqual([], backend.command_TAG(self.files[1], "test_untag_indirect__ok2"))

        self.assertListEqual([], backend.command_ASSIGN_SUBTAGS("test_untag_indirect__ok1", ["test_untag_indirect__ok2"]))
        self.assertListEqual([], backend.command_UNTAG(self.files[1], "test_untag_indirect__ok1"))
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag']), 1)

    def test_untag_not_tagged(self):
        self.assertEqual(1, len(backend.command_UNTAG(self.files[0], "test_untag_not_tagged")))
        backend.command_TAG(self.files[0], "test_untag_not_tagged")
        self.assertEqual(1, len(backend.command_UNTAG(self.files[0], "test_untag_not_tagged2")))
        self.assertEqual(0, len(backend.command_UNTAG(self.files[0], "test_untag_not_tagged")))

    def test_untag_nonexistent_file(self):
        filepath = self.loc + "nonexistent_file.txt"
        self.assertEqual(1, len(backend.command_TAG(filepath, "test_tag_nonexistent_file")))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag'], [])

    def test_untag_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag']), 2)
        self.assertEqual(0, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertEqual(len(table['file']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))
        self.assertEqual(0, len(backend.command_UNTAG(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertEqual(len(table['rel_file_tag']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_subtag_ok(self):
        superior_tag = "test_subtag_ok_superior"
        inferior_tag = "test_subtag_ok_inferior"
        self.assertEqual(0, len(backend.command_TAG(self.files[0], superior_tag)))
        self.assertEqual(0, len(backend.command_TAG(self.files[1], inferior_tag)))
        self.assertEqual(0, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_nonexistent_superior(self):
        inferior_tag = "test_subtag_nonexistent_superior_inferior"
        self.assertEqual(0, len(backend.command_TAG(self.files[0], inferior_tag)))
        self.assertEqual(1, len(backend.command_ASSIGN_SUBTAGS("test_subtag_nonexistent_superior_superior", [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_subtag_nonexistent_inferior(self):
        superior_tag = "test_subtag_nonexistent_inferior_superior"
        self.assertEqual(0, len(backend.command_TAG(self.files[0], superior_tag)))
        self.assertEqual(1, len(backend.command_ASSIGN_SUBTAGS(superior_tag, ["test_subtag_nonexistent_inferior_inferior"])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_subtag_already_subtagged(self):
        superior_tag = "test_subtag_already_subtagged_superior"
        inferior_tag = "test_subtag_already_subtagged_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        self.assertEqual(0, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        self.assertEqual(1, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_reverse_subtagged(self):
        superior_tag = "test_subtag_reverse_subtagged_superior"
        inferior_tag = "test_subtag_reverse_subtagged_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        self.assertEqual(0, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        self.assertEqual(1, len(backend.command_ASSIGN_SUBTAGS(inferior_tag, [superior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_ok_and_common_file(self):
        superior_tag = "test_subtag_ok_and_common_file_superior"
        inferior_tag = "test_subtag_ok_and_common_file_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[0], inferior_tag)
        self.assertEqual(0, len(backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag']), 1)



