#!/usr/bin/env python3

from . import database as db, os_calls, validator as v, settings, errors
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

def command_TAG(file_name : str, tag_name : str) -> list[str]:
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return [type(e).__name__ + ": " + str(e)]

    database = db.Database(settings.database_path)
    validator = v.Validator(database)
    
    permit = validator.approved_tag_operation(file_system, inode, file_name, tag_name)
    if not permit.approved:
        logger.info(f"Tag operation not approved for file ({file_name}) and tag '{tag_name}'")
        return permit.data
    
    original_tags = database._direct_tags_for_file(file_system, inode)
    known_superiors = database.get_superiors_tree(tag_name)

    database.new_rel_file_tag(file_system, inode, tag_name)
    logger.info(f"Tagged file ({file_name}) with tag '{tag_name}'")

    for original_tag in original_tags:
        if original_tag in known_superiors:
            command_UNTAG(file_name, original_tag)

    return []

def command_UNTAG(file_name : str, tag_name : str) -> list[str]:
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return [type(e).__name__ + ": " + str(e)]
    
    database = db.Database(settings.database_path)
    validator = v.Validator(database)
    
    permit = validator.approved_untag_operation(file_system, inode, tag_name, file_name)
    if not permit.approved:
        logger.info(f"Untag operation not approved for file ({file_name}) and tag '{tag_name}'")
        return permit.data
    
    for tag in permit.data:
        database.delete_rel_file_tag(file_system, inode, tag)
        logger.info(f"Untagged file ({file_name}) from subtag '{tag}'")
    logger.info(f"Untagged file ({file_name}) from tag '{tag_name}'")

    if validator.file_is_isolated(file_system, inode):
        logger.info(f"File ({file_name}) is now isolated. Deleting file record.")
        database.delete_file(file_system, inode)
    return []

def command_DEL_TAG(tag_name : str) -> list[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    permit = validator.approved_del_tag_operation(tag_name)
    if not permit.approved:
        logger.info(f"Delete tag operation not approved for tag '{tag_name}'")
        return permit.data
    
    affected_files = database._direct_files_for_tag(tag_name)
    database.delete_tag(tag_name)
    logger.info(f"Deleted tag '{tag_name}' from database.")

    for (file_system, inode, filename) in affected_files:
        if validator.file_is_isolated(file_system, inode):
            logger.info(f"File is now isolated. Deleting file record.")
            database.delete_file(file_system, inode)
    return []

def command_ASSIGN_SUBTAGS(superior_tag_name : str, inferior_tags : list[str]) -> list[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    failures = []
    for inferior_tag_name in inferior_tags:
        permit = validator.approved_subtag_operation(superior_tag_name, inferior_tag_name)
        if not permit.approved:
            failures.append((inferior_tag_name, permit.data))
            logger.info(f"Assign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            continue
        database.new_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Assigned inferior tag '{inferior_tag_name}' to superior tag '{superior_tag_name}'")

        for (file_system, inode, unconfirmed_path) in database._direct_files_for_tag(inferior_tag_name):
            permit = validator.approved_direct_untag_operation(file_system, inode, superior_tag_name, unconfirmed_path)
            if permit.approved:
                database.delete_rel_file_tag(file_system, inode, superior_tag_name)
            logger.info(f"Untagged file ({unconfirmed_path}) from subtag '{superior_tag_name}'")
    return failures

def command_UNASSIGN_SUBTAGS(superior_tag_name : str, inferior_tags : list[str]) -> list[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    failures = []
    for inferior_tag_name in inferior_tags:
        permit = validator.approved_unsubtag_operation(superior_tag_name, inferior_tag_name)
        if not permit.approved:
            logger.info(f"Unassign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            failures.append((inferior_tag_name, permit.data))
            continue
        database.delete_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Unassigned inferior tag '{inferior_tag_name}' from superior tag '{superior_tag_name}'")
    return failures

def query_LIST_EXISTING_TAGS() -> set[str]:
    database = db.Database(settings.database_path)
    return database.get_tags()

def query_LIST_TAGS_FOR_FILE(file_name : str) -> set[str]:
    database = db.Database(settings.database_path)
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return {type(e).__name__ + ": " + str(e)}
    
    database = db.Database(settings.database_path)
    validator = v.Validator(database)
    permit = validator.approved_list_for_file_operation(file_system, inode, file_name)
    if not permit.approved:
        logger.info(f"List tags for file operation not approved for file '{file_name}'")
        return set()
    
    output = database.get_tags_for_file(file_system, inode)
    return output
    
def query_LIST_FILES(query : str) -> list[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not query:
        logger.info(f"List files operation with empty query. Outputting all files.")
        raw_output = database.get_filepaths()
        user_output = [x[2] for x in raw_output]
        return user_output

    instruction_list = validator.parse_query(query)
    
    return list(process_query_instruction(instruction_list))



def process_query_instruction(level_data):
    if isinstance(level_data, set):
        return level_data
    if isinstance(level_data, str):
        return query_LIST_FILES_FOR_TAG(level_data)
    
    if len(level_data) != 3:
        raise errors.NecessaryUpstreamInterrupt("Incorrect instruction level: " + level_data)
    
    operator = level_data[1]
    operand1 = process_query_instruction(level_data[0])
    operand2 = process_query_instruction(level_data[2])

    match(operator):
        case "&":
            return operand1.intersection(operand2)
        case "|":
            return operand1.union(operand2)
        case "/":
            return operand1.difference(operand2)
        case _:
            raise errors.NecessaryUpstreamInterrupt("Incorrect operator: " + operator + ", in expression: " + level_data)
        

def query_LIST_FILES_FOR_TAG(tag_name : str) -> set:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_tag_operation(tag_name):
        logger.info(f"List files for tag operation not approved for tag '{tag_name}'")
        raise errors.NecessaryUpstreamInterrupt
    
    output = database.get_files_for_tag(tag_name)
    return output

def query_LIST_DIRECT_SUBTAGS(superior_tag_name : str) -> set[str]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    if not validator.approved_list_for_tag_operation(superior_tag_name):
        logger.info(f"List direct subtags operation not approved for tag '{superior_tag_name}'")
        return set()
    return database._direct_inferiors_for_tag(superior_tag_name)
    
def query_LIST_RECURSIVE_SUBTAGS(root_tag_name : str) -> dict[str, dict]:
    database = db.Database(settings.database_path)
    validator = v.Validator(database)

    def get_subtag_dict(super_tag):
        if not validator.approved_list_for_tag_operation(super_tag):
            return {}
        subtag_dict = {}
        queue = database._direct_inferiors_for_tag(super_tag)
        for subtag in queue:
            subtag_dict[subtag] = get_subtag_dict(subtag)
        return subtag_dict
    
    subtag_hierarchy = get_subtag_dict(root_tag_name)
    return subtag_hierarchy

def query_LIST_ROOTS() -> set[str]:
    database = db.Database(settings.database_path)
    return database.get_root_tags()

def query_LIST_HIERARCHY() -> dict[str, dict]: 
    hierarchy = {}
    for root_tag in query_LIST_ROOTS():
        hierarchy[root_tag] = query_LIST_RECURSIVE_SUBTAGS(root_tag)
    return hierarchy


