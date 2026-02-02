#!/usr/bin/env python3

from . import database
class Validator:
    def __init__(self, database : database.Database):
        self.database = database

    def tag_exists(self, tag_name : str) -> bool:
        return tag_name in self.database.list_tags()

    def file_exists(self, file_system, inode : int) -> bool:
        return inode in self.database.list_files()

    def file_has_tag(self, file_system, inode : int, tag_name : str) -> bool:
        return tag_name in self.database.list_tags_for_file(file_system, inode)

    def tag_has_direct_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        return inf_tag_name in self.database.list_subtags_for_tag(super_tag_name)

    def tag_has_superiority(self, super_tag_name : str, inf_tag_name : str) -> bool:
        queue = self.database.list_subtags_for_tag(super_tag_name)
        if inf_tag_name in queue:
            return True
        
        for tag in queue:
            if self.tag_has_superiority(tag, inf_tag_name):
                return True
        return False
    
    def file_is_isolated(self, file_system, inode : int) -> bool:
        return len(self.database.list_tags_for_file(file_system, inode)) == 0
    
    def tag_is_isolated(self, tag_name : str) -> bool:
        no_attached_files = len(self.database.list_files_for_tag(tag_name)) == 0
        no_superiors = len(self.database.list_superior_tags_for_tag(tag_name)) == 0
        no_inferiors = len(self.database.list_subtags_for_tag(tag_name)) == 0
        return no_attached_files and no_superiors and no_inferiors

    def approved_tag_operation(self, file_system, inode, tag) -> bool:
        if not self.tag_exists(tag):
            # log
            self.database.new_tag(tag)

        if not self.file_exists(file_system, inode):
            self.database.new_file(file_system, inode)

        permit = not self.file_has_tag(file_system, inode, tag)
        # logging.debug(f"Approved tag operation for file ({file_system}, {inode}) and tag '{tag}': {permit}")
        return permit
        

    def approved_untag_operation(self, file_system, inode, tag) -> bool:
        permit = ( self.file_exists(file_system, inode) and self.file_has_tag(file_system, inode, tag) )
        # logging.debug(f"Approved untag operation for file ({file_system}, {inode}) and tag '{tag}': {permit}")
        return permit

    def approved_list_for_tag_operation(self, tag_name) -> bool:
        return self.tag_exists(tag_name)

    def approved_list_for_file_operation(self, file_system, inode) -> bool:
        return self.file_exists(file_system, inode)

    def approved_del_tag_operation(self, tag_name) -> bool:
        return self.tag_exists(tag_name)

    def approved_subtag_operation(self, super_tag_name, inf_tag_name) -> bool:
        if not self.tag_exists(super_tag_name):
            return False
        if not self.tag_exists(inf_tag_name):
            self.database.new_tag(inf_tag_name)
        conflicting_hierarchy = (self.tag_has_direct_superiority(super_tag_name, inf_tag_name) or self.tag_has_superiority(inf_tag_name, super_tag_name))
        return not conflicting_hierarchy

    def approved_unsubtag_operation(self, super_tag_name, inf_tag_name) -> bool:
        if not self.tag_exists(super_tag_name) or not self.tag_exists(inf_tag_name):
            return False
        return self.tag_has_direct_superiority(super_tag_name, inf_tag_name)

   
