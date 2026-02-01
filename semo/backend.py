#!/usr/bin/env python3

from . import database as db, os_calls, validator as v, errors as e, settings

def command_TAG(file_name : str, tag_name : str):
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        raise Exception

    database = db.Database(settings.database_path)
    validator = v.Validator(database)
    
    if not validator.approved_tag_operation(file_system, inode, tag_name):
        return False
    database.new_rel_file_tag(file_system, inode, tag_name)


def command_UNTAG(file_name : str, tag_name : str):
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        raise Exception

    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_untag_operation(file_system, inode, tag_name):
        return False
    
    database.delete_rel_file_tag(file_system, inode, tag_name)

    remaining_tags = len(database.list_tags_for_file(file_system, inode))
    if remaining_tags == 0: database.delete_file(file_system, inode)

    remaining_files = len(database.list_files_for_tag(tag_name))
    if remaining_files == 0: database.delete_tag(tag_name)

def command_LIST_EXISTING_TAGS():
    database = db.Database(settings.database_path)
    return database.list_tags()

def command_LIST_TAGS_FOR_FILE(file_name : str):
    database = db.Database(settings.database_path)
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        raise Exception
    
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_file_operation(file_system, inode):
        return []
    
    return database.list_tags_for_file(file_system, inode)

def command_DEL_TAG(tag_name : str):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_del_tag_operation(tag_name):
        return False
    
    affected_files = database.list_files_for_tag(tag_name)
    database.delete_tag(tag_name)
    for (file_system, inode) in affected_files:
        if validator.file_is_isolated(file_system, inode):
            database.delete_file(file_system, inode)

def command_ASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    for inferior_tag_name in inferior_tags:
        if not validator.approved_subtag_operation(superior_tag_name, inferior_tag_name):
            continue
        database.new_rel_tag_tag(superior_tag_name, inferior_tag_name)

def command_UNASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    for inferior_tag_name in inferior_tags:
        if not validator.approved_unsubtag_operation(superior_tag_name, inferior_tag_name):
            continue
        database.delete_rel_tag_tag(superior_tag_name, inferior_tag_name)
        if validator.tag_is_isolated(inferior_tag_name):
            database.delete_tag(inferior_tag_name)
    if validator.tag_is_isolated(superior_tag_name):
        database.delete_tag(superior_tag_name)

def command_LIST_DIRECT_SUBTAGS(superior_tag_name : str):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_tag_operation(superior_tag_name):
        return []
    return database.list_subtags_for_tag(superior_tag_name)
    
def command_LIST_RECURSIVE_SUBTAGS(root_tag_name : str):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.tag_exists(root_tag_name):
        raise e.TagNotInDatabaseError

    def get_subtag_dict(super_tag):
        subtag_dict = {}
        queue = database.list_subtags_for_tag(super_tag)
        for subtag in queue:
            subtag_dict[subtag] = get_subtag_dict(subtag)
        return subtag_dict
    
    subtag_hierarchy = get_subtag_dict(root_tag_name)
    return subtag_hierarchy

def command_LIST_HIERARCHY():
    database = db.Database(settings.database_path)
    hierarchy = {}
    for root_tag in database.list_root_tags():
        hierarchy[root_tag] = command_LIST_RECURSIVE_SUBTAGS(root_tag)
    return hierarchy
