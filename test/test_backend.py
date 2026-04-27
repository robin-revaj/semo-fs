import unittest
import os
from semo import backend
from semo import database as db, utils

class TestCommandBackend(unittest.TestCase):
    def setUp(self):
        self.path = utils.get_test_db()
        utils.set_working_db(self.path)
        self.DB = db.Database(self.path)
        self.DB.init_create_script()
        self.loc = "test/data/"
        files = [open(self.loc + "file1.txt", "x"), open(self.loc + "file2.txt", "x"), open(self.loc + "file3.txt", "x")]
        self.files = []
        for f in files:
            self.files.append(f.name)
            f.close()
    def tearDown(self):
        os.remove(self.path)
        utils.set_working_db(utils.get_default_db())
        for f in self.files:
            os.remove(f)

    def test_tag_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_tag_ok", None))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_ok", None)])
        self.assertListEqual(table['rel_file_tag_null'], [(1, 1, 1)])

    def test_tag_str_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_tag_str_ok", "s42"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_str_ok", "str")])
        self.assertListEqual(table['rel_file_tag_str'], [(1, 1, 1, "s42")])

    def test_tag_int_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_tag_int_ok", 42))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_int_ok", "int")])
        self.assertListEqual(table['rel_file_tag_int'], [(1, 1, 1, 42)])

    def test_tag_already_tagged(self):
        filepath = self.files[0]
        self.assertEqual(0, len(backend.connect_tag(filepath, "test_tag_already_tagged")))
        self.assertListEqual([f"{filepath} already tagged test_tag_already_tagged"], backend.connect_tag(filepath, "test_tag_already_tagged"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_already_tagged", None)])
        self.assertListEqual(table['rel_file_tag_null'], [(1, 1, 1)])

    def test_tag_str_already_tagged(self):
        filepath = self.files[0]
        self.assertEqual(0, len(backend.connect_tag(filepath, "test_tag_already_tagged", "s42")))
        self.assertListEqual([f"{filepath} already tagged test_tag_already_tagged"], backend.connect_tag(filepath, "test_tag_already_tagged", "s43"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_already_tagged", "str")])
        self.assertListEqual(table['rel_file_tag_str'], [(1, 1, 1, "s42")])

    def test_tag_int_already_tagged(self):
        filepath = self.files[0]
        self.assertEqual(0, len(backend.connect_tag(filepath, "test_tag_already_tagged", 42)))
        self.assertListEqual([f"{filepath} already tagged test_tag_already_tagged"], backend.connect_tag(filepath, "test_tag_already_tagged", 43))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, "test_tag_already_tagged", "int")])
        self.assertListEqual(table['rel_file_tag_int'], [(1, 1, 1, 42)])

    def test_tag_nonexistent_file(self):
        filepath = self.loc + "nonexistent_file.txt"
        self.assertEqual(1, len(backend.connect_tag(filepath, "test_tag_nonexistent_file")))
        self.assertEqual(1, len(backend.connect_tag(filepath, "test_tag_nonexistent_file", "s1")))
        self.assertEqual(1, len(backend.connect_tag(filepath, "test_tag_nonexistent_file", 1)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag_null'], [])
        self.assertListEqual(table['rel_file_tag_str'], [])
        self.assertListEqual(table['rel_file_tag_int'], [])

    def test_tag_tagged_with_superior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.connect_tag(self.files[0], inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag_null']), 2)
        self.assertEqual(len(table['file']), 2)
        
        id, fs, inode, path = table['file'][0]
        self.assertSetEqual({inferior_tag}, self.DB._direct_tags_for_file(fs, inode))
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))

    def test_tag_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(1, len(backend.connect_tag(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag_null']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag}, self.DB._direct_tags_for_file(fs, inode))
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))

    def test_untag_direct_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_untag_direct_ok"))
        self.assertListEqual([], backend.disconnect_tag(filepath, "test_untag_direct_ok"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag_null'], [])

    def test_untag_str_direct_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_untag_direct_ok", "s42"))
        self.assertListEqual([], backend.disconnect_tag(filepath, "test_untag_direct_ok"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag_str'], [])

    def test_untag_int_direct_ok(self):
        filepath = self.files[0]
        self.assertListEqual([], backend.connect_tag(filepath, "test_untag_direct_ok", 42))
        self.assertListEqual([], backend.disconnect_tag(filepath, "test_untag_direct_ok"))
        table = self.DB.dump_tables()
        self.assertListEqual(table['file'], [])
        self.assertListEqual(table['rel_file_tag_int'], [])
    
    def test_untag_indirect_ok(self):
        self.assertListEqual([], backend.connect_tag(self.files[0], "test_untag_indirect__ok1"))
        self.assertListEqual([], backend.connect_tag(self.files[1], "test_untag_indirect__ok2"))

        self.assertListEqual([], backend.connect_subtags("test_untag_indirect__ok1", ["test_untag_indirect__ok2"]))
        self.assertListEqual([], backend.disconnect_tag(self.files[1], "test_untag_indirect__ok1"))
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_null']), 1)

    def test_untag_str_indirect_ok(self):
        self.assertListEqual([], backend.connect_tag(self.files[0], "test_untag_indirect__ok1", "s1"))
        self.assertListEqual([], backend.connect_tag(self.files[1], "test_untag_indirect__ok2", "s2"))

        self.assertListEqual([], backend.connect_subtags("test_untag_indirect__ok1", ["test_untag_indirect__ok2"]))
        self.assertListEqual([], backend.disconnect_tag(self.files[1], "test_untag_indirect__ok1"))
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_str']), 1)

    def test_untag_int_indirect_ok(self):
        self.assertListEqual([], backend.connect_tag(self.files[0], "test_untag_indirect__ok1", 1))
        self.assertListEqual([], backend.connect_tag(self.files[1], "test_untag_indirect__ok2", 2))

        self.assertListEqual([], backend.connect_subtags("test_untag_indirect__ok1", ["test_untag_indirect__ok2"]))
        self.assertListEqual([], backend.disconnect_tag(self.files[1], "test_untag_indirect__ok1"))
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_int']), 1)        

    def test_untag_not_tagged(self):
        self.assertEqual(1, len(backend.disconnect_tag(self.files[0], "test_untag_not_tagged")))
        backend.connect_tag(self.files[0], "test_untag_not_tagged")
        self.assertEqual(1, len(backend.disconnect_tag(self.files[0], "test_untag_not_tagged2")))
        self.assertEqual(0, len(backend.disconnect_tag(self.files[0], "test_untag_not_tagged")))

    def test_untag_nonexistent_file(self):
        filepath = self.loc + "nonexistent_file.txt"
        self.assertEqual(1, len(backend.disconnect_tag(filepath, "test_tag_nonexistent_file")))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['file'], [])

    def test_untag_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_null']), 2)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertEqual(len(table['file']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))
        self.assertEqual(0, len(backend.disconnect_tag(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertEqual(len(table['rel_file_tag_null']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_untag_str_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.connect_tag(self.files[0], superior_tag, "s1")
        backend.connect_tag(self.files[1], inferior_tag, "s2")
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_str']), 2)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "str"), (2, inferior_tag, "str")])
        self.assertEqual(len(table['file']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))
        self.assertEqual(0, len(backend.disconnect_tag(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "str"), (2, inferior_tag, "str")])
        self.assertEqual(len(table['rel_file_tag_str']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_untag_int_tagged_with_inferior(self):
        superior_tag = "test_tag_tagged_with_superior_superior"
        inferior_tag = "test_tag_tagged_with_superior_inferior"
        backend.connect_tag(self.files[0], superior_tag, 1)
        backend.connect_tag(self.files[1], inferior_tag, 2)
        table = self.DB.dump_tables()
        self.assertEqual(len(table['rel_file_tag_int']), 2)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "int"), (2, inferior_tag, "int")])
        self.assertEqual(len(table['file']), 2)
        id, fs, inode, path = table['file'][1]
        self.assertSetEqual({inferior_tag, superior_tag}, self.DB.get_tags_for_file(fs, inode))
        self.assertEqual(0, len(backend.disconnect_tag(self.files[1], superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "int"), (2, inferior_tag, "int")])
        self.assertEqual(len(table['rel_file_tag_int']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_subtag_ok(self):
        superior_tag = "test_subtag_ok_superior"
        inferior_tag = "test_subtag_ok_inferior"
        self.assertEqual(0, len(backend.connect_tag(self.files[0], superior_tag)))
        self.assertEqual(0, len(backend.connect_tag(self.files[1], inferior_tag)))
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_nonexistent_superior(self):
        inferior_tag = "test_subtag_nonexistent_superior_inferior"
        self.assertEqual(0, len(backend.connect_tag(self.files[0], inferior_tag)))
        self.assertEqual(1, len(backend.connect_subtags("test_subtag_nonexistent_superior_superior", [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_subtag_nonexistent_inferior(self):
        superior_tag = "test_subtag_nonexistent_inferior_superior"
        self.assertEqual(0, len(backend.connect_tag(self.files[0], superior_tag)))
        self.assertEqual(1, len(backend.connect_subtags(superior_tag, ["test_subtag_nonexistent_inferior_inferior"])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_subtag_already_subtagged(self):
        superior_tag = "test_subtag_already_subtagged_superior"
        inferior_tag = "test_subtag_already_subtagged_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        self.assertEqual(1, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_reverse_subtagged(self):
        superior_tag = "test_subtag_reverse_subtagged_superior"
        inferior_tag = "test_subtag_reverse_subtagged_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        self.assertEqual(1, len(backend.connect_subtags(inferior_tag, [superior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])

    def test_subtag_ok_and_common_file(self):
        superior_tag = "test_subtag_ok_and_common_file_superior"
        inferior_tag = "test_subtag_ok_and_common_file_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[0], inferior_tag)
        self.assertEqual(0, len(backend.connect_subtags(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [(1, 1, 2)])
        self.assertEqual(len(table['rel_file_tag_null']), 1)

    def test_unsubtag_ok(self):
        superior_tag = "test_unsubtag_ok_superior"
        inferior_tag = "test_unsubtag_ok_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.disconnect_subtags(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_nonexistent_superior(self):
        inferior_tag = "test_unsubtag_nonexistent_superior_inferior"
        self.assertEqual(0, len(backend.connect_tag(self.files[0], inferior_tag)))
        self.assertEqual(1, len(backend.disconnect_subtags("test_unsubtag_nonexistent_superior_superior", [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_nonexistent_inferior(self):
        superior_tag = "test_unsubtag_nonexistent_inferior_superior"
        self.assertEqual(0, len(backend.connect_tag(self.files[0], superior_tag)))
        self.assertEqual(1, len(backend.disconnect_subtags(superior_tag, ["test_unsubtag_nonexistent_inferior_inferior"])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_unsubtag_not_subtagged(self):
        superior_tag = "test_unsubtag_not_subtagged_superior"
        inferior_tag = "test_unsubtag_not_subtagged_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        self.assertEqual(1, len(backend.disconnect_subtags(superior_tag, [inferior_tag])))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None), (2, inferior_tag, None)])
        self.assertListEqual(table['rel_tag_tag'], [])

    def test_del_tag_ok(self):
        tag_name = "test_del_tag_ok"
        backend.connect_tag(self.files[0], tag_name)
        self.assertEqual(0, len(backend.delete_tag(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag_null'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_str_ok(self):
        tag_name = "test_del_tag_ok"
        backend.connect_tag(self.files[0], tag_name, "s1")
        self.assertEqual(0, len(backend.delete_tag(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag_str'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_int_ok(self):
        tag_name = "test_del_tag_ok"
        backend.connect_tag(self.files[0], tag_name, 1)
        self.assertEqual(0, len(backend.delete_tag(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag_int'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_nonexistent(self):
        tag_name = "test_del_tag_nonexistent"
        self.assertEqual(1, len(backend.delete_tag(tag_name)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [])
        self.assertListEqual(table['rel_file_tag_null'], [])
        self.assertListEqual(table['rel_file_tag_str'], [])
        self.assertListEqual(table['rel_file_tag_int'], [])
        self.assertListEqual(table['file'], [])

    def test_del_tag_with_subtags(self):
        superior_tag = "test_del_tag_with_subtags_superior"
        inferior_tag = "test_del_tag_with_subtags_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(2, inferior_tag, None)])
        self.assertEqual(len(table['rel_file_tag_null']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_with_overtags(self):
        superior_tag = "test_del_tag_with_overtags_superior"
        inferior_tag = "test_del_tag_with_overtags_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, None)])
        self.assertEqual(len(table['rel_file_tag_null']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_str_with_subtags(self):
        superior_tag = "test_del_tag_with_subtags_superior"
        inferior_tag = "test_del_tag_with_subtags_inferior"
        backend.connect_tag(self.files[0], superior_tag, "s1")
        backend.connect_tag(self.files[1], inferior_tag, "s2")
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(2, inferior_tag, "str")])
        self.assertEqual(len(table['rel_file_tag_str']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_str_with_overtags(self):
        superior_tag = "test_del_tag_with_overtags_superior"
        inferior_tag = "test_del_tag_with_overtags_inferior"
        backend.connect_tag(self.files[0], superior_tag, "s1")
        backend.connect_tag(self.files[1], inferior_tag, "s2")
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "str")])
        self.assertEqual(len(table['rel_file_tag_str']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_int_with_subtags(self):
        superior_tag = "test_del_tag_with_subtags_superior"
        inferior_tag = "test_del_tag_with_subtags_inferior"
        backend.connect_tag(self.files[0], superior_tag, 1)
        backend.connect_tag(self.files[1], inferior_tag, 2)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(superior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(2, inferior_tag, "int")])
        self.assertEqual(len(table['rel_file_tag_int']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_del_tag_int_with_overtags(self):
        superior_tag = "test_del_tag_with_overtags_superior"
        inferior_tag = "test_del_tag_with_overtags_inferior"
        backend.connect_tag(self.files[0], superior_tag, 1)
        backend.connect_tag(self.files[1], inferior_tag, 2)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertEqual(0, len(backend.delete_tag(inferior_tag)))
        table = self.DB.dump_tables()
        self.assertListEqual(table['tag'], [(1, superior_tag, "int")])
        self.assertEqual(len(table['rel_file_tag_int']), 1)
        self.assertEqual(len(table['file']), 1)

    def test_list_all_tags(self):
        tag1 = "test_list_all_tags1"
        tag2 = "test_list_all_tags2"
        tag3 = "test_list_all_tags3"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2, "tag2")
        backend.connect_tag(self.files[2], tag3, 3)
        self.assertSetEqual({tag1, tag2, tag3}, backend.get_all_tags())

    def test_list_tags_for_file_ok(self):
        tag1 = "test_list_all_tags1"
        tag2 = "test_list_all_tags2"
        tag3 = "test_list_all_tags3"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2, "tag2")
        backend.connect_tag(self.files[0], tag3, 3)
        self.assertSetEqual({tag1, tag2, tag3}, backend.get_tags_for_file(self.files[0]))

    def test_list_tags_for_file_nonexistent(self):
        self.assertEqual(1, len(backend.get_tags_for_file(self.loc + "nonexistent_file.txt")))

    def test_list_tags_for_file_inherited(self):
        superior_tag = "test_list_tags_for_file_inherited_superior"
        inferior_tag = "test_list_tags_for_file_inherited_inferior"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag)
        backend.connect_subtags(superior_tag, [inferior_tag])
        self.assertSetEqual({superior_tag, inferior_tag}, backend.get_tags_for_file(self.files[1]))

    def test_list_files_no_query(self):
        tag1 = "test_list_files_no_query1"
        tag2 = "test_list_files_no_query2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_files(""))

    def test_list_files_query_singular(self):
        tag1 = "test_list_files_query_singular1"
        tag2 = "test_list_files_query_singular2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[0]}, backend.query_files(tag1))
        self.assertSetEqual({self.files[1]}, backend.query_files(tag2))

    def test_list_files_query_singular_nonexistent(self):
        self.assertSetEqual(set(), backend.query_files("test_list_files_query_singular_nonexistent"))

    def test_list_files_query_AND(self):
        tag1 = "test_list_files_query_AND1"
        tag2 = "test_list_files_query_AND2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag1)
        self.assertSetEqual({self.files[0]}, backend.query_files(f"{tag1} & {tag2}"))

    def test_list_files_query_AND_parentheses(self):
        tag1 = "test_list_files_query_AND_parentheses1"
        tag2 = "test_list_files_query_AND_parentheses2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag1)
        self.assertSetEqual({self.files[0]}, backend.query_files(f"({tag1} & {tag2})"))

    def test_list_files_query_AND_nonexistent(self):
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))
        backend.connect_tag(self.files[0], "test_list_files_query_AND_nonexistent1")
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))
        backend.delete_tag("test_list_files_query_AND_nonexistent1")
        backend.connect_tag(self.files[0], "test_list_files_query_AND_nonexistent2")
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_AND_nonexistent1 & test_list_files_query_AND_nonexistent2"))

    def test_list_files_query_OR(self):
        tag1 = "test_list_files_query_OR1"
        tag2 = "test_list_files_query_OR2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_files(f"{tag1} | {tag2}"))

    def test_list_files_query_OR_parentheses(self):
        tag1 = "test_list_files_query_OR_parentheses1"
        tag2 = "test_list_files_query_OR_parentheses2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_files(f"({tag1} | {tag2})"))

    def test_list_files_query_OR_nonexistent(self):
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))
        backend.connect_tag(self.files[0], "test_list_files_query_OR_nonexistent1")
        self.assertSetEqual({self.files[0]}, backend.query_files(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))
        backend.delete_tag("test_list_files_query_OR_nonexistent1")
        backend.connect_tag(self.files[0], "test_list_files_query_OR_nonexistent2")
        self.assertSetEqual({self.files[0]}, backend.query_files(f"test_list_files_query_OR_nonexistent1 | test_list_files_query_OR_nonexistent2"))

    def test_list_files_query_NOT(self):
        tag1 = "test_list_files_query_NOT1"
        tag2 = "test_list_files_query_NOT2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag1)
        self.assertSetEqual({self.files[1]}, backend.query_files(f"{tag1} / {tag2}"))
        self.assertSetEqual(set(), backend.query_files(f"{tag2} / {tag1}"))

    def test_list_files_query_NOT_parentheses(self):
        tag1 = "test_list_files_query_NOT_parentheses1"
        tag2 = "test_list_files_query_NOT_parentheses2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag1)
        self.assertSetEqual({self.files[1]}, backend.query_files(f"({tag1} / {tag2})"))
        self.assertSetEqual(set(), backend.query_files(f"({tag2} / {tag1})"))
    
    def test_list_files_query_NOT_nonexistent(self):
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))
        backend.connect_tag(self.files[0], "test_list_files_query_NOT_nonexistent1")
        self.assertSetEqual({self.files[0]}, backend.query_files(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))
        backend.delete_tag("test_list_files_query_NOT_nonexistent1")
        backend.connect_tag(self.files[0], "test_list_files_query_NOT_nonexistent2")
        self.assertSetEqual(set(), backend.query_files(f"test_list_files_query_NOT_nonexistent1 / test_list_files_query_NOT_nonexistent2"))

    def test_list_files_query_combined_parenthesized(self):
        tag1 = "test_list_files_query_combined1"
        tag2 = "test_list_files_query_combined2"
        tag3 = "test_list_files_query_combined3"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag3)
        backend.connect_tag(self.files[1], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[1]}, backend.query_files(f"({tag1} & {tag2}) & {tag3}"))
        self.assertSetEqual({self.files[0], self.files[1]}, backend.query_files(f"{tag1} & {tag2}"))
        self.assertSetEqual({self.files[0]}, backend.query_files(f"{tag1} & ({tag2} / {tag3})"))
        self.assertSetEqual({self.files[1]}, backend.query_files(f"({tag1}  | {tag2}) & ({tag1} & {tag3})"))

    def test_list_files_query_combined(self):
        tag1 = "test_list_files_query_combined1"
        tag2 = "test_list_files_query_combined2"
        tag3 = "test_list_files_query_combined3"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[0], tag2)
        backend.connect_tag(self.files[1], tag3)
        backend.connect_tag(self.files[1], tag1)
        backend.connect_tag(self.files[1], tag2)
        self.assertSetEqual({self.files[1]}, backend.query_files(f"{tag1} & {tag2} & {tag3}"))
        self.assertSetEqual({self.files[0]}, backend.query_files(f"{tag1} & {tag2} / {tag3}"))
        self.assertSetEqual({self.files[1]}, backend.query_files(f"({tag1}  | {tag2}) & {tag1} & {tag3}"))
        self.assertSetEqual({self.files[0]}, backend.query_files(f"({tag1}  | {tag2}) & {tag1} / {tag3}"))

    def test_list_files_query_wrong(self):
        tag1 = "test_list_files_query_wrong1"
        tag2 = "test_list_files_query_wrong2"
        backend.connect_tag(self.files[0], tag1)
        backend.connect_tag(self.files[1], tag2)
        with self.assertRaises(Exception):
            self.assertSetEqual(set(), backend.query_files(f"{tag1} {tag2}"))
        with self.assertRaises(Exception):
            backend.query_files(f"{tag1} / {tag2} l {tag1}")
        with self.assertRaises(Exception):
            backend.query_files(f"{tag1} &")
        with self.assertRaises(Exception):
            backend.query_files(f"& {tag1}")
        with self.assertRaises(Exception):
            backend.query_files(f"({tag1} |")

    def test_list_subtags_direct_ok(self):
        superior_tag = "test_list_subtags_ok_superior"
        inferior_tag1 = "test_list_subtags_ok_inferior1"
        inferior_tag2 = "test_list_subtags_ok_inferior2"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag1)
        backend.connect_tag(self.files[2], inferior_tag2)
        backend.connect_subtags(superior_tag, [inferior_tag1, inferior_tag2])
        self.assertSetEqual({inferior_tag1, inferior_tag2}, backend.get_subtags_DIRECT(superior_tag))

    def test_list_subtags_direct_nonexistent_superior(self):
        self.assertSetEqual(set(), backend.get_subtags_DIRECT("test_list_subtags_direct_nonexistent_superior"))

    def test_list_subtags_indirect_ok(self):
        superior_tag = "test_list_subtags_indirect_ok_superior"
        inferior_tag1 = "test_list_subtags_indirect_ok_inferior1"
        inferior_tag2 = "test_list_subtags_indirect_ok_inferior2"
        backend.connect_tag(self.files[0], superior_tag)
        backend.connect_tag(self.files[1], inferior_tag1)
        backend.connect_tag(self.files[2], inferior_tag2)
        backend.connect_subtags(superior_tag, [inferior_tag1])
        backend.connect_subtags(inferior_tag1, [inferior_tag2])
        self.assertSetEqual({inferior_tag1}, backend.get_subtags_DIRECT(superior_tag))
        self.assertDictEqual({inferior_tag1: {inferior_tag2: {}}}, backend.get_subtags(superior_tag))

    
    



