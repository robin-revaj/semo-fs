#!/usr/bin/env python3

def tag_exists(database, tag_name : str):
    return tag_name in database.list_tags()

def file_exists(database, file_system, inode : int):
    return inode in database.list_files()

def file_has_tag(database, file_system, inode : int, tag_name : str):
    return tag_name in database.list_tags_for_file(file_system, inode)

def tags_have_hierarchy(database, super_tag_name : str, inf_tag_name : str):
    return inf_tag_name in database.list_subtags_for_tags(super_tag_name)

# TODO
def hierarchy_not_circular(database, super_tag_name : str, inf_tag_name : str):
    return True



def approve_tag_operation(database, file_system, inode, tag):
    pass

def approve_untag_operation(database, file_system, inode, tag):
    pass

def approve_list_for_file_operation(database, file_system, inode):
    pass

def approve_del_tag_operation(database, tag_name):
    pass

def approve_subtag_operation(database, super_tag_name, inf_tag_name):
    pass

def approve_unsubtag_operation(database, super_tag_name, inf_tag_name):
    pass

def approve_list_for_tag_operation(database, super_tag_name):
    pass
