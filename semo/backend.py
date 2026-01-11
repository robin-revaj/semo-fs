#!/usr/bin/env python3

import database as db
import os_calls
import validator
import errors as e
import settings

def command_TAG(file_name : str, tag_name : str):
    database = db.Database(settings.database_path)

    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        raise e.FileNotInDatabaseError
    
    if not validator.tag_exists(database, tag_name):
        # TODO how do this. the handler shouldnt be doing UI actions 
        # if not interface.user_confirmation("Tag {0} does not exist yet. Do you want to create it?".format(tag_name)):
        #     raise e.OperationCancelledError
        database.new_tag(tag_name)

    if not validator.file_exists(database, file_system, inode):
        database.new_file(file_system, inode)
        
    if validator.file_has_tag(database, file_system, inode, tag_name):
        raise e.RelationshipExistsError
    
    database.new_rel_file_tag(file_system, inode, tag_name)


def command_UNTAG(file_name : str, tag_name : str):
    database = db.Database(settings.database_path)

    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        raise e.FileNotInDatabaseError
    
    if not validator.file_exists(database, file_system, inode) or not validator.file_has_tag(database, file_system, inode, tag_name):
        raise e.RelationshipDoesntExistError
    
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
        raise e.FileNotInDatabaseError
    
    if not validator.file_exists(db, file_system, inode):
        return []
    
    return database.list_tags_for_file(file_system, inode)

def command_DEL_TAG(tag_name : str):
    database = db.Database(settings.database_path)
    if not validator.tag_exists(database, tag_name):
        raise e.TagNotInDatabaseError
    database.delete_tag(tag_name)

def command_ASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)

    passed = []

    if not validator.tag_exists(database, superior_tag_name):
        raise e.TagNotInDatabaseError
    for inferior_tag_name in inferior_tags:
        if not validator.hierarchy_not_circular(database, superior_tag_name, inferior_tag_name):
            pass
        if not validator.tag_exists(database, inferior_tag_name):
            database.new_tag(inferior_tag_name)
        if validator.tags_have_hierarchy(database, superior_tag_name, inferior_tag_name):
            passed.append(inferior_tag_name)
            continue
        database.new_rel_tag_tag(superior_tag_name, inferior_tag_name)

def command_UNASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)

    passed = []

    if not validator.tag_exists(database, superior_tag_name):
        raise e.TagNotInDatabaseError
    for inferior_tag_name in inferior_tags:
        if not validator.tag_exists(database, inferior_tag_name):
            raise e.TagNotInDatabaseError
        if not validator.tags_have_hierarchy(database, superior_tag_name, inferior_tag_name):
            passed.append(inferior_tag_name)
            continue
        database.delete_rel_tag_tag(superior_tag_name, inferior_tag_name)

def command_LIST_DIRECT_SUBTAGS(superior_tag_name : str):
    database = db.Database(settings.database_path)
    if not validator.tag_exists(database, superior_tag_name):
        raise e.TagNotInDatabaseError
    return database.list_subtags_for_tag(superior_tag_name)
    
def command_LIST_RECURSIVE_SUBTAGS(root_tag_name : str):
    database = db.Database(settings.database_path)
    if not validator.tag_exists(database, root_tag_name):
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
