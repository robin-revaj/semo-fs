#!/usr/bin/env python3

from . import database as db, os_calls, validator as v, settings
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

# database = db.Database(settings.database_path)
# validator = v.Validator(database)

def command_TAG(file_name : str, tag_name : str):
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        logger.exception(f"Failed to retrieve inode for file '{file_name}'")
        return

    database = db.Database(settings.database_path)
    validator = v.Validator(database)
    
    if not validator.approved_tag_operation(file_system, inode, tag_name):
        logger.info(f"Tag operation not approved for file ({file_name}) and tag '{tag_name}'")
        return
    
    database.new_rel_file_tag(file_system, inode, tag_name)
    logger.info(f"Tagged file ({file_name}) with tag '{tag_name}'")
def command_UNTAG(file_name : str, tag_name : str):
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        logger.exception(f"Failed to retrieve inode for file '{file_name}'")
        return

    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_untag_operation(file_system, inode, tag_name):
        logger.info(f"Untag operation not approved for file ({file_name}) and tag '{tag_name}'")
        return
    
    database.delete_rel_file_tag(file_system, inode, tag_name)
    logger.info(f"Untagged file ({file_name}) from tag '{tag_name}'")
    if validator.file_is_isolated(file_system, inode):
        logger.info(f"File ({file_name}) is now isolated. Deleting file record.")
        database.delete_file(file_system, inode)

    if validator.tag_is_isolated(tag_name):
        logger.info(f"Tag '{tag_name}' is now isolated. Deleting tag record.")
        database.delete_tag(tag_name)

def command_DEL_TAG(tag_name : str):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_del_tag_operation(tag_name):
        logger.info(f"Delete tag operation not approved for tag '{tag_name}'")
        return
    
    affected_files = database.list_files_for_tag(tag_name)
    database.delete_tag(tag_name)
    logger.info(f"Deleted tag '{tag_name}' from database.")

    for (file_system, inode) in affected_files:
        if validator.file_is_isolated(file_system, inode):
            logger.info(f"File is now isolated. Deleting file record.")
            database.delete_file(file_system, inode)

def command_ASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    for inferior_tag_name in inferior_tags:
        if not validator.approved_subtag_operation(superior_tag_name, inferior_tag_name):
            logger.info(f"Assign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            continue
        database.new_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Assigned inferior tag '{inferior_tag_name}' to superior tag '{superior_tag_name}'") 


def command_UNASSIGN_SUBTAG(superior_tag_name : str, inferior_tags : list[str]):
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    for inferior_tag_name in inferior_tags:
        if not validator.approved_unsubtag_operation(superior_tag_name, inferior_tag_name):
            logger.info(f"Unassign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            continue
        database.delete_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Unassigned inferior tag '{inferior_tag_name}' from superior tag '{superior_tag_name}'")
        if validator.tag_is_isolated(inferior_tag_name):
            logger.info(f"Inferior tag '{inferior_tag_name}' is now isolated. Deleting tag record.")
            database.delete_tag(inferior_tag_name)
    if validator.tag_is_isolated(superior_tag_name):
        logger.info(f"Superior tag '{superior_tag_name}' is now isolated. Deleting tag record.")
        database.delete_tag(superior_tag_name)


def query_LIST_EXISTING_TAGS() -> list[str]:
    database = db.Database(settings.database_path)
    return database.list_tags()

def query_LIST_TAGS_FOR_FILE(file_name : str) -> list[str]:
    database = db.Database(settings.database_path)
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception:
        logger.exception(f"Failed to retrieve inode for file '{file_name}'")
        return []
    
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_file_operation(file_system, inode):
        logger.info(f"List tags for file operation not approved for file '{file_name}'")
        return []
    
    return database.list_tags_for_file(file_system, inode)

def query_LIST_DIRECT_SUBTAGS(superior_tag_name : str) -> list[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_tag_operation(superior_tag_name):
        logger.info(f"List direct subtags operation not approved for tag '{superior_tag_name}'")
        return []
    return database.list_subtags_for_tag(superior_tag_name)
    
def query_LIST_RECURSIVE_SUBTAGS(root_tag_name : str) -> dict[str, dict]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    def get_subtag_dict(super_tag):
        if not validator.approved_list_for_tag_operation(super_tag):
            return {}
        subtag_dict = {}
        queue = database.list_subtags_for_tag(super_tag)
        for subtag in queue:
            subtag_dict[subtag] = get_subtag_dict(subtag)
        return subtag_dict
    
    subtag_hierarchy = get_subtag_dict(root_tag_name)
    return subtag_hierarchy

def query_LIST_ROOTS() -> list[str]:
    database = db.Database(settings.database_path)
    return database.list_root_tags()

def query_LIST_HIERARCHY() -> dict[str, dict]: 
    hierarchy = {}
    for root_tag in query_LIST_ROOTS():
        hierarchy[root_tag] = query_LIST_RECURSIVE_SUBTAGS(root_tag)
    return hierarchy


