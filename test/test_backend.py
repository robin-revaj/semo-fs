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

    def test_unsubtag_ok(self):
        superior_tag = "test_unsubtag_ok_superior"
        inferior_tag = "test_unsubtag_ok_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.command_UNASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_nonexistent_superior(self):
        inferior_tag = "test_unsubtag_nonexistent_superior_inferior"
        self.assertEqual(0, len(backend.command_TAG(self.files[0], inferior_tag)))
        self.assertEqual(1, len(backend.command_UNASSIGN_SUBTAGS("test_unsubtag_nonexistent_superior_superior", [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_nonexistent_inferior(self):
        superior_tag = "test_unsubtag_nonexistent_inferior_superior"
        self.assertEqual(0, len(backend.command_TAG(self.files[0], superior_tag)))
        self.assertEqual(1, len(backend.command_UNASSIGN_SUBTAGS(superior_tag, ["test_unsubtag_nonexistent_inferior_inferior"])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_not_subtagged(self):
        superior_tag = "test_unsubtag_not_subtagged_superior"
        inferior_tag = "test_unsubtag_not_subtagged_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        self.assertEqual(1, len(backend.command_UNASSIGN_SUBTAGS(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag), (2, inferior_tag)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_del_tag_ok(self):
        tag_name = "test_del_tag_ok"
        backend.command_TAG(self.files[0], tag_name)
        self.assertEqual(0, len(backend.command_DEL_TAG(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_nonexistent(self):
        tag_name = "test_del_tag_nonexistent"
        self.assertEqual(1, len(backend.command_DEL_TAG(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_with_subtags(self):
        superior_tag = "test_del_tag_with_subtags_superior"
        inferior_tag = "test_del_tag_with_subtags_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.command_DEL_TAG(superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(2, inferior_tag)])
        self.assertEqual(len(table['rel_file_tag']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_with_overtags(self):
        superior_tag = "test_del_tag_with_overtags_superior"
        inferior_tag = "test_del_tag_with_overtags_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.command_DEL_TAG(inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag)])
        self.assertEqual(len(table['rel_file_tag']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_list_all_tags(self):
        tag1 = "test_list_all_tags1"
        tag2 = "test_list_all_tags2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({tag1, tag2}, backend.query_LIST_ALL_TAGS())

    def test_list_tags_for_file_ok(self):
        tag1 = "test_list_tags_for_file_ok1"
        tag2 = "test_list_tags_for_file_ok2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        self.assertSetEqual({tag1, tag2}, backend.query_LIST_TAGS_FOR_FILE(self.files[0]))

    def test_list_tags_for_file_nonexistent(self):
        self.assertEqual(1, len(backend.query_LIST_TAGS_FOR_FILE(self.loc + "nonexistent_file.txt")))

    def test_list_tags_for_file_inherited(self):
        superior_tag = "test_list_tags_for_file_inherited_superior"
        inferior_tag = "test_list_tags_for_file_inherited_inferior"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag])
        self.assertSetEqual({superior_tag, inferior_tag}, backend.query_LIST_TAGS_FOR_FILE(self.files[1]))

    def test_list_files_no_query(self):
        tag1 = "test_list_files_no_query1"
        tag2 = "test_list_files_no_query2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_LIST_FILES(""))

    def test_list_files_query_singular(self):
        tag1 = "test_list_files_query_singular1"
        tag2 = "test_list_files_query_singular2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(tag1))
        self.assertSetEqual({self.files[1]}, backend.query_LIST_FILES(tag2))

    def test_list_files_query_singular_nonexistent(self):
        self.assertSetEqual(set(), backend.query_LIST_FILES("test_list_files_query_singular_nonexistent"))

    def test_list_files_query_AND(self):
        tag1 = "test_list_files_query_AND1"
        tag2 = "test_list_files_query_AND2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        backend.command_TAG(self.files[1], tag1)
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"{tag1} & {tag2}"))

    def test_list_files_query_AND_parentheses(self):
        tag1 = "test_list_files_query_AND_parentheses1"
        tag2 = "test_list_files_query_AND_parentheses2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        backend.command_TAG(self.files[1], tag1)
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"({tag1} & {tag2})"))

    def test_list_files_query_AND_nonexistent(self):
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))
        backend.command_TAG(self.files[0], "test_list_files_query_AND_nonexistent1")
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))
        backend.command_DEL_TAG("test_list_files_query_AND_nonexistent1")
        backend.command_TAG(self.files[0], "test_list_files_query_AND_nonexistent2")
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))

    def test_list_files_query_OR(self):
        tag1 = "test_list_files_query_OR1"
        tag2 = "test_list_files_query_OR2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_LIST_FILES(f"{tag1} | {tag2}"))

    def test_list_files_query_OR_parentheses(self):
        tag1 = "test_list_files_query_OR_parentheses1"
        tag2 = "test_list_files_query_OR_parentheses2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_LIST_FILES(f"({tag1} | {tag2})"))

    def test_list_files_query_OR_nonexistent(self):
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))
        backend.command_TAG(self.files[0], "test_list_files_query_OR_nonexistent1")
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))
        backend.command_DEL_TAG("test_list_files_query_OR_nonexistent1")
        backend.command_TAG(self.files[0], "test_list_files_query_OR_nonexistent2")
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))

    def test_list_files_query_NOT(self):
        tag1 = "test_list_files_query_NOT1"
        tag2 = "test_list_files_query_NOT2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        backend.command_TAG(self.files[1], tag1)
        self.assertSetEqual({self.files[1]}, backend.query_LIST_FILES(f"{tag1} / {tag2}"))
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"{tag2} / {tag1}"))

    def test_list_files_query_NOT_parentheses(self):
        tag1 = "test_list_files_query_NOT_parentheses1"
        tag2 = "test_list_files_query_NOT_parentheses2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        backend.command_TAG(self.files[1], tag1)
        self.assertSetEqual({self.files[1]}, backend.query_LIST_FILES(f"({tag1} / {tag2})"))
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"({tag2} / {tag1})"))
    
    def test_list_files_query_NOT_nonexistent(self):
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))
        backend.command_TAG(self.files[0], "test_list_files_query_NOT_nonexistent1")
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))
        backend.command_DEL_TAG("test_list_files_query_NOT_nonexistent1")
        backend.command_TAG(self.files[0], "test_list_files_query_NOT_nonexistent2")
        self.assertSetEqual(set(), backend.query_LIST_FILES(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))

    def test_list_files_query_combined(self):
        tag1 = "test_list_files_query_combined1"
        tag2 = "test_list_files_query_combined2"
        tag3 = "test_list_files_query_combined3"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[0], tag2)
        backend.command_TAG(self.files[1], tag3)
        backend.command_TAG(self.files[1], tag1)
        backend.command_TAG(self.files[1], tag2)
        self.assertSetEqual({self.files[1]}, backend.query_LIST_FILES(f"({tag1} & {tag2}) & {tag3}"))
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_LIST_FILES(f"{tag1} & {tag2}"))
        self.assertSetEqual({self.files[0]}, backend.query_LIST_FILES(f"{tag1} & ({tag2} / {tag3})"))
        self.assertSetEqual({self.files[1]}, backend.query_LIST_FILES(f"({tag1} | {tag2}) & ({tag1} & {tag3})"))

    def test_list_files_query_wrong(self):
        tag1 = "test_list_files_query_wrong1"
        tag2 = "test_list_files_query_wrong2"
        backend.command_TAG(self.files[0], tag1)
        backend.command_TAG(self.files[1], tag2)
        with self.assertRaises(Exception):
            self.assertSetEqual(set(), backend.query_LIST_FILES(f"{tag1} {tag2}"))
        with self.assertRaises(Exception):
            backend.query_LIST_FILES(f"{tag1} / {tag2} / {tag1}")
        with self.assertRaises(Exception):
            backend.query_LIST_FILES(f"{tag1} / {tag2} * {tag1}")
        with self.assertRaises(Exception):
            backend.query_LIST_FILES(f"{tag1} &")
        with self.assertRaises(Exception):
            backend.query_LIST_FILES(f"& {tag1}")
        with self.assertRaises(Exception):
            backend.query_LIST_FILES(f"({tag1} |")

    def test_list_subtags_direct_ok(self):
        superior_tag = "test_list_subtags_ok_superior"
        inferior_tag1 = "test_list_subtags_ok_inferior1"
        inferior_tag2 = "test_list_subtags_ok_inferior2"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag1)
        backend.command_TAG(self.files[2], inferior_tag2)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag1, inferior_tag2])
        self.assertSetEqual({inferior_tag1, inferior_tag2}, backend.query_LIST_DIRECT_SUBTAGS(superior_tag))

    def test_list_subtags_direct_nonexistent_superior(self):
        self.assertSetEqual(set(), backend.query_LIST_DIRECT_SUBTAGS("test_list_subtags_direct_nonexistent_superior"))

    def test_list_subtags_indirect_ok(self):
        superior_tag = "test_list_subtags_indirect_ok_superior"
        inferior_tag1 = "test_list_subtags_indirect_ok_inferior1"
        inferior_tag2 = "test_list_subtags_indirect_ok_inferior2"
        backend.command_TAG(self.files[0], superior_tag)
        backend.command_TAG(self.files[1], inferior_tag1)
        backend.command_TAG(self.files[2], inferior_tag2)
        backend.command_ASSIGN_SUBTAGS(superior_tag, [inferior_tag1])
        backend.command_ASSIGN_SUBTAGS(inferior_tag1, [inferior_tag2])
        self.assertSetEqual({inferior_tag1}, backend.query_LIST_DIRECT_SUBTAGS(superior_tag))
        self.assertDictEqual({inferior_tag1: {inferior_tag2: {}}}, backend.query_LIST_ALL_SUBTAGS(superior_tag))

    
    



