#!/usr/bin/env python3

from . import database

class Validator:
    def __init__(self, database : database.Database):
        self.database = database

    def tag_exists(self, tag_name : str):
        return tag_name in self.database.list_tags()

    def file_exists(self, file_system, inode : int):
        return inode in self.database.list_files()

    def file_has_tag(self, file_system, inode : int, tag_name : str):
        return tag_name in self.database.list_tags_for_file(file_system, inode)

    def tags_have_hierarchy(self, super_tag_name : str, inf_tag_name : str):
        return inf_tag_name in self.database.list_subtags_for_tag(super_tag_name)


    def approved_tag_operation(self, file_system, inode, tag):
        if not self.tag_exists(tag):
            self.database.new_tag(tag)

        if not self.file_exists(file_system, inode):
            self.database.new_file(file_system, inode)

        return not self.file_has_tag(file_system, inode, tag)
        

    def approved_untag_operation(self, file_system, inode, tag):
        return ( self.file_exists(file_system, inode) and self.file_has_tag(file_system, inode, tag) )

    def approved_list_for_tag_operation(self, tag_name):
        return self.tag_exists(tag_name)

    def approved_list_for_file_operation(self, file_system, inode):
        return self.file_exists(file_system, inode)

    def approved_del_tag_operation(self, tag_name):
        return self.tag_exists(tag_name)

    def approved_subtag_operation(self, super_tag_name, inf_tag_name):
        if not self.tag_exists(super_tag_name):
            return False
        if not self.tag_exists(inf_tag_name):
            self.database.new_tag(inf_tag_name)
        conflicting_hierarchy = (self.tags_have_hierarchy(super_tag_name, inf_tag_name) or self.tags_have_hierarchy(inf_tag_name, super_tag_name))
        return not conflicting_hierarchy

    def approved_unsubtag_operation(self, super_tag_name, inf_tag_name):
        if not self.tag_exists(super_tag_name) or not self.tag_exists(inf_tag_name):
            return False
        return self.tags_have_hierarchy(super_tag_name, inf_tag_name)

   
