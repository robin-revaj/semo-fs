#!.venv/bin/python3

from semo import database as db, os_calls, validator as v, settings, errors, utils
import logging 

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger.addHandler(file_handler)

def connect_tag(file_name : str, tag_name : str, value = None) -> list[str]:
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return [type(e).__name__ + ": " + str(e)]

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
        
    permit = validator.approved_tag_operation(file_system, inode, file_name, tag_name, value)
    if not permit.approved:
        logger.info(f"Tag operation not approved for file ({file_name}) and tag '{tag_name}'")
        return permit.data
    
    original_tags = database._direct_tags_for_file(file_system, inode)
    known_superiors = database.get_superiors_tree(tag_name)

    database.new_rel_file_tag(file_system, inode, tag_name, value)
    logger.info(f"Tagged file ({file_name}) with tag '{tag_name}'")

    for original_tag in original_tags:
        if original_tag in known_superiors:
            disconnect_tag(file_name, original_tag)

    return []

def disconnect_tag(file_name : str, tag_name : str) -> list[str]:
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return [type(e).__name__ + ": " + str(e)]
    
    database = db.Database(utils.get_working_db())
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

def delete_tag(tag_name : str) -> list[str]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_del_tag_operation(tag_name)
    if not permit.approved:
        logger.info(f"Delete tag operation not approved for tag '{tag_name}'")
        return permit.data
    
    affected_files = database._direct_files_for_tag(tag_name)
    database.delete_tag(tag_name)
    logger.info(f"Deleted tag '{tag_name}' from database.")

    for (file_system, inode, filename, id) in affected_files:
        if validator.file_is_isolated(file_system, inode):
            logger.info(f"File is now isolated. Deleting file record.")
            database.delete_file(file_system, inode)
    return []

def connect_subtags(superior_tag_name : str, inferior_tags : list[str]) -> list[str]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    failures = []
    for inferior_tag_name in inferior_tags:
        permit = validator.approved_subtag_operation(superior_tag_name, inferior_tag_name)
        if not permit.approved:
            failures.append((f"for pair {superior_tag_name}, {inferior_tag_name}", permit.data))
            logger.info(f"Assign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            continue
        database.new_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Assigned inferior tag '{inferior_tag_name}' to superior tag '{superior_tag_name}'")

        for (file_system, inode, unconfirmed_path, id) in database._direct_files_for_tag(inferior_tag_name):
            permit = validator.approved_direct_untag_operation(file_system, inode, superior_tag_name, unconfirmed_path)
            if permit.approved:
                database.delete_rel_file_tag(file_system, inode, superior_tag_name)
            logger.info(f"Untagged file ({unconfirmed_path}) from subtag '{superior_tag_name}'")
    return failures

def disconnect_subtags(superior_tag_name : str, inferior_tags : list[str]) -> list[str]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    failures = []
    for inferior_tag_name in inferior_tags:
        permit = validator.approved_unsubtag_operation(superior_tag_name, inferior_tag_name)
        if not permit.approved:
            logger.info(f"Unassign subtag operation not approved for superior tag '{superior_tag_name}' and inferior tag '{inferior_tag_name}'")
            failures.append((f"for pair {superior_tag_name}, {inferior_tag_name}", permit.data))
            continue
        database.delete_rel_tag_tag(superior_tag_name, inferior_tag_name)
        logger.info(f"Unassigned inferior tag '{inferior_tag_name}' from superior tag '{superior_tag_name}'")
    return failures

def get_all_tags() -> set[str]:
    database = db.Database(utils.get_working_db())
    return database.get_tags()

def get_tags_for_file(file_name : str) -> set[str]:
    database = db.Database(utils.get_working_db())
    try:
        file_system, inode = os_calls.retrieve_inode_from_path(file_name)
    except Exception as e:
        return {type(e).__name__ + ": " + str(e)}
    
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    permit = validator.approved_list_for_file_operation(file_system, inode, file_name)
    if not permit.approved:
        logger.info(f"List tags for file operation not approved for file '{file_name}'")
        return set()
    
    output = database.get_tags_for_file(file_system, inode)
    return output

def query_files(query : str, long_format = False) -> set[str]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    if query:
        instruction_list = validator.parse_query(query)
        return process_query_instruction(instruction_list)

    logger.info(f"List files operation with empty query. Outputting all files.")
    raw_output = database.get_files_with_paths()
    if long_format:
        user_output = { (file_system, inode, verified_path(file_system, inode, unconfirmed_path)) for (file_system, inode, unconfirmed_path) in raw_output }
    else:
        user_output = { verified_path(file_system, inode, unconfirmed_path) for (file_system, inode, unconfirmed_path) in raw_output }
    return user_output

def process_query_instruction(level_data):
    if isinstance(level_data, set):
        return level_data
    if isinstance(level_data, str):
        return get_files_for_tag(level_data)
    
    if len(level_data) == 1:
        return process_query_instruction(level_data[0])
    if len(level_data) != 3:
        raise errors.NecessaryUpstreamInterrupt("Incorrect instruction level: " + str(level_data))
    
    operator = level_data[1]
    operand1 = process_query_instruction(level_data[0])
    operand2 = process_query_instruction(level_data[2])

    match(operator):
        case "&":
            return operand1.intersection(operand2)
        case "|" | "+":
            return operand1.union(operand2)
        case "/" | "-":
            return operand1.difference(operand2)
        case _:
            raise errors.NecessaryUpstreamInterrupt("Incorrect operator: " + operator + ", in expression: " + " ".join(level_data))
        
def verified_path(file_system, inode, unconfirmed_path):
    try:
        file_system_check, inode_check = os_calls.retrieve_inode_from_path(unconfirmed_path)
        if file_system_check != file_system or inode_check != inode:
            return f"File formerly at {unconfirmed_path}."
        return unconfirmed_path
    except Exception as e:
        logger.info(f"Failed to verify path for file ({file_system}, {inode}). Error: {type(e).__name__} - {str(e)}. Returning unconfirmed path '{unconfirmed_path}'")
        return f"File formerly at {unconfirmed_path}."

def get_files_for_tag_DIRECT(tag_name : str, long_format : bool = False) -> set:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(tag_name)
    logger.info(f"Approved - List files for tag direct operation ({tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    raw_output = database._direct_files_for_tag(tag_name)
    if long_format:
        return raw_output
    return { unconfirmed_path for (file_system, inode, unconfirmed_path, id) in raw_output }

def get_files_for_tag(tag_name : str, limit_to_direct : bool = False, long_format : bool = False) -> set:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(tag_name)
    logger.info(f"Approved - List files for tag operation ({tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    
    raw_output = database.get_files_for_tag(tag_name)
    if long_format:
        return raw_output
    user_output = { unconfirmed_path for (file_system, inode, unconfirmed_path, id) in raw_output }
    return user_output

def get_subtags_DIRECT(superior_tag_name : str) -> set[str]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(superior_tag_name)
    logger.info(f"Approved - List direct subtags operation ({superior_tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    return database._direct_inferiors_for_tag(superior_tag_name)
    
def get_subtags(root_tag_name : str) -> dict[str, dict]:
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    def get_subtag_dict(super_tag):
        permit = validator.approved_list_for_tag_operation(super_tag)
        if not permit.approved:
            return {}
        subtag_dict = {}
        queue = database._direct_inferiors_for_tag(super_tag)
        for subtag in queue:
            subtag_dict[subtag] = get_subtag_dict(subtag)
        return subtag_dict
    
    subtag_hierarchy = get_subtag_dict(root_tag_name)
    return subtag_hierarchy

def get_roots() -> set[str]:
    database = db.Database(utils.get_working_db())
    return database.get_root_tags()

def get_file_by_id(id : int) -> tuple[int, int, str, int] | None:
    database = db.Database(utils.get_working_db())
    return database.get_file_by_id(id)