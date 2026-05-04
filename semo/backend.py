#! /usr/bin/env python3

"""Module provides backend of user functions, in detail handles interacting with the database and content

File should be imported as a module and contains the following functions:

    * connect_tag - connects tag with file if permitted
    * disconnect_tag - disconnects tag from file if permitted
    * delete_tag - deletes tag from database if permitted
    * connect_subtags - connects tag with subtag if permitted
    * disconnect_subtags - disconnects tag from subtag if permitted
    * get_all_tags - returns all tags in database
    * get_tags_for_file - returns tags (including inherited) corresponding to file if permitted
    * get_subtags_DIRECT - returns direct subtags for tag if permitted
    * get_subtags - returns all (including inherited) subtags for tag if permitted
    * get_roots - returns root tags in database
    * get_file_by_id - returns file data for entry identified by id if permitted
    * query_files - returns files corresponding to query if permitted
    * _query_parse_instruction_set - parses query into readable format
    * _query_read_level - processes one level of instruction set
    * _query_resolve_set_operation - processes set operation on two operands
    * _query_resolve_operand - resolves operand into set of files
    * _query_resolve_condition - resolves condition operand into set of files
    * get_files_for_tag_DIRECT - returns files corresponding directly to a tag
    * get_rels_for_tag - returns files corresponding to a tag (including inherited)
    * get_files_for_directory - returns files with tag relationships located in given directory tree
    * daemon_pid - returns process ID of semo watcher process
    * watch_directory - adds watch to watchlist and signals watcher process to register change
    * unwatch_directory - removes watch from watchlist and signals watcher process to register change
    * recover_under_directory - attempts to retrieve lost or outdated data from directory files
    * clean_records - deletes inconsistent, damaged, outdated entries from database
    * export_data_to_xattr - export tags to files' extended attributes
    * import_data_from_xattr - import tags from files' extended attributes

"""

import database as db, validator as v, utils, data_repair
from utils import SemoException
import logging, pyparsing, os, subprocess, signal

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

file_handler = logging.FileHandler(utils.get_log_file())
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(utils.get_log_format()))

logger.addHandler(file_handler)

# INPUT

def connect_tag(file_name : str, tag_name : str, value = None) -> list[str]:
    """Creates file-tag relationship with provided value.

    If permitted by validator, calls database function to add entry for file-tag relationship.
    If tag has subtag relationship, function then handles cleaning them.

    Parameters
    ----------
    file_name : str
        Path to file
    tag_name : str
        Name of new or existing tag
    value : str | int | None, optional
        Value of relationship, default is None
    
    Returns
    -------
    list[str]
        Empty if executed successfully, otherwise contains error messages
    """

    try:
        file_system, inode = utils.get_fsid_and_inode(file_name)
    except SemoException as e:
        return [type(e).__name__ + ": " + str(e)]

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    if utils.is_integer_string(value):
        value = int(value)  # type: ignore
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
    """Removes file-tag relationship.

    If permitted by validator, calls database function to remove entry for file-tag relationship.
    If file has no more relationship, function then deletes it from database.

    Parameters
    ----------
    file_name : str
        Path to file
    tag_name : str
        Name of tag
    
    Returns
    -------
    list[str]
        Empty if executed successfully, otherwise contains error messages
    """
    
    try:
        file_system, inode = utils.get_fsid_and_inode(file_name)
    except SemoException as e:
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
    """Deletes tag and all its relationships.

    If permitted by validator, calls database function to remove entries for tag.
    It then cleans up its relationships.

    Parameters
    ----------
    tag_name : str
        Name of tag
    
    Returns
    -------
    list[str]
        Empty if executed successfully, otherwise contains error messages
    """
    
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
    """Creates superior-inferior tag relationships.

    If permitted by validator, calls database function to create entries for tag-tag relationships.
    Handles subsequent cleanup of their relationships.

    Parameters
    ----------
    superior_tag_name : str
        Name of superior tag
    inferior_tags : list[str]
        Names of inferior tags
    
    Returns
    -------
    list[str]
        Empty if executed successfully, otherwise contains error messages
    """
    
    
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
    """Removes superior-inferior tag relationships.

    If permitted by validator, calls database function to remove entries for tag-tag relationships.

    Parameters
    ----------
    superior_tag_name : str
        Name of superior tag
    inferior_tags : list[str]
        Names of inferior tags
    
    Returns
    -------
    list[str]
        Empty if executed successfully, otherwise contains error messages
    """
    
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

# OUTPUT

def get_all_tags() -> set[str]:
    """Gets and returns set of all tags in database
    
    Returns
    -------
    set[str]
        Set of tag names
    """
    
    database = db.Database(utils.get_working_db())
    return database.get_tags()

def get_tags_for_file(file_name : str) -> dict:
    """Gets and returns dictionary of tags and their values for a given file
    
    If permitted by validator, calls database function to list tag:value relationships for file
    
    Parameters
    ----------
    file_name : str
        Path to file

    Returns
    -------
    dict[str : str | int | None]
        Dictionary with tag names as keys and values as values
    """
    
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    file_system, inode = utils.get_fsid_and_inode(file_name)
    
    permit = validator.approved_list_for_file_operation(file_system, inode, file_name)
    if not permit.approved:
        logger.info(f"List tags for file operation not approved for file '{file_name}'")
        return {}
    
    return database.get_rels_for_file(file_system, inode)

def get_subtags_DIRECT(superior_tag_name : str) -> set[str]:
    """Gets and returns set of direct subtags for given tag

    If permitted by validator, calls database function to list direct subtag entries for superior tag

    Parameters
    ----------
    superior_tag_name : str
        Name of superior tag
    
    Returns
    -------
    set[str]
        Set of inferior tag names
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(superior_tag_name)
    logger.info(f"Approved - List direct subtags operation ({superior_tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    return database._direct_inferiors_for_tag(superior_tag_name)
    
def get_subtags(root_tag_name : str) -> dict[str, dict]:
    """Gets and returns dictionary hierarchy of all subtags for given tag

    If permitted by validator, calls database function to list subtag entries for superior tag

    Parameters
    ----------
    root_tag_name : str
        Name of superior tag
    
    Returns
    -------
    dict[str, dict]
        Subtag hierarchy for superior tag
    """

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
    """Gets and returns set of root tags
    
    Returns
    -------
    set[str]
        Set of root tags in database
    """

    database = db.Database(utils.get_working_db())
    return database.get_root_tags()

def get_file_by_id(id : int) -> tuple[int, int, str, int] | None:
    """Gets and returns file by database ID
    
    Returns
    -------
    tuple[int, int, str, int] | None
        (fsid, inode, filepath, entry_id)
    """

    database = db.Database(utils.get_working_db())
    return database.get_file_by_id(id)

def query_files(query : str, shortened_output = True) -> set[tuple]:
    """Processes query, retrieves corresponding files and returns set of value:file pairs

    Parameters
    ----------
    query : str
        Tag query. If query is empty, all files will be returned
    shortened_output : bool, optional
        If true, return in simplified format
    
    Returns
    -------
    set(tuple)
        Set of data per file in tuples
    """
    
    if not query:
        query = " | ".join(get_roots())

    instruction_list = _query_parse_instruction_set(query)
    raw_output = _query_read_level(instruction_list)
    
    if shortened_output:
        return {(val, path) for (_, _, path, _, val) in raw_output}
    return raw_output
    
def _query_parse_instruction_set(query : str) -> list:
    """Validates query string and parses it into nested list 

    Parameters
    ----------
    query : str

    Returns
    -------
    list
        List of strings or nested lists
    
    Raises
    ------
    SemoException
        In case of incorrect query
    """

    operand = pyparsing.Word(pyparsing.alphanums + "_-")
    set_operator = pyparsing.one_of("& * | + / -")
    cond_operator = pyparsing.one_of("== >= <= > <")
    expression = pyparsing.infix_notation(operand, [(cond_operator, 2, pyparsing.opAssoc.LEFT), (set_operator, 2, pyparsing.opAssoc.LEFT)])
    try:
        output = expression.parse_string(query, parse_all=True).as_list()
    except pyparsing.exceptions.ParseException as e:
        raise SemoException("Malformed query: ", str(e))    
    if len(output) == 1 and isinstance(output[0], list):
        output = output[0]
    return output

def _query_read_level(level_data : list) -> set[tuple]:
    """Processes a single level of query instruction list.
    
    Parameters
    ----------
    level_data : list
        List of strings or nested lists
    
    Returns
    -------
    set[tuple]
        Set of file data

    Raises
    ------
    SemoException
        If query level is somehow malformed
    """

    if len(level_data) == 1:
        return _query_resolve_operand(level_data[0])
    if len(level_data) < 3:
        raise SemoException("wrong query read: ", level_data)
    op1 = level_data.pop(0)

    while level_data:
        operator, op2 = level_data.pop(0), level_data.pop(0)
        if operator in "& * | + / -":
            if isinstance(op1, list):
                set1 = _query_read_level(op1)
            else: set1 = _query_resolve_operand(op1)
            if isinstance(op2, list):
                set2 = _query_read_level(op2)
            else: set2 = _query_resolve_operand(op2)
            op1 = _query_resolve_set_operation( set1, operator, set2 )
        else:
            var : str = str(op1)
            condition : str | int = op2
            op1 = _query_resolve_condition( var, operator, condition )
        
    return op1

def _query_resolve_set_operation(operand1 : set, operator : str, operand2 : set) -> set:
    """Handle set operations
    
    Parameters
    ----------
    operand1 : set
    operator : str
    operand2 : set
    
    Returns
    -------
    set[tuple]
        Set of file data

    Raises
    ------
    SemoException
        If operator is incorrect
    """
    
    match (operator):
        case "&" | "*":
            return operand1.intersection(operand2)
        case "|" | "+":
            return operand1.union(operand2)
        case "/" | "-":
            return operand1.difference(operand2)
        case _:
            raise SemoException("Incorrect operator: " + operator)

def _query_resolve_operand(operand : str | set) -> set:
    """Translates operand to set of file data
    
    Parameters
    ----------
    operand : str | set
    
    Returns
    -------
    set[tuple]
        Set of file data

    Raises
    ------
    SemoException
        If operand is somehow malformed
    """

    if isinstance(operand, set): return operand
    if isinstance(operand, str): return get_rels_for_tag(operand, path_only_output=False)
    raise SemoException("wrong operand type: ", operand)

def _query_resolve_condition(tag_name : str, operation : str, value : int | str) -> set:
    """Translates a condition operand into set of file data.
    
    Parameters
    ----------
    tag_name : str
    operation : str
    value : str | int
    
    Returns
    -------
    set[tuple]
        Set of file data

    Raises
    ------
    SemoException
        If condition is incorrect, eg. comparing incompatible types
    """
    
    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_conditional_list_for_tag_operation(tag_name, value)
    if not permit.approved:
        raise SemoException(f"tag {tag_name} type incompatible with '{value}'")
    match database.get_tag_type(tag_name):
        case "int":
            value = int(value)
            return database._int_rels_for_tag_condition(tag_name, operation, value)
        case "str":
            if operation != "==":
                raise SemoException(f"string value {value} not comparable")
            value = str(value)
            return database._str_rels_for_tag_condition(tag_name, value)
    raise SemoException(f"type '{value}' not comparable")    

def get_files_for_tag_DIRECT(tag_name : str, path_only_output = True) -> set:
    """Gets and returns set of files directly connected with given tag

    If permitted by validator, calls database function to list direct file relationships for tag

    Parameters
    ----------
    tag_name : str
        Name of tag
    path_only_output : bool, optional
        If True, returns file data in shortened format. Default is True
    Returns
    -------
    set[str] | set[tuple]
        Set of filepaths or set of file data in tuples
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(tag_name)
    logger.info(f"Approved - List files for tag direct operation ({tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    raw_output = database._direct_files_for_tag(tag_name)
    if not path_only_output:
        return raw_output
    return { unconfirmed_path for (file_system, inode, unconfirmed_path, id) in raw_output }

def get_rels_for_tag(tag_name : str, path_only_output : bool = True) -> set:
    """Gets and returns set of files connected with given tag (including inherited)

    If permitted by validator, calls database function to list file relationships for tag

    Parameters
    ----------
    tag_name : str
        Name of tag
    path_only_output : bool, optional
        If True, returns file data in shortened format. Default is True
    Returns
    -------
    set[str] | set[tuple]
        Set of filepaths or set of file data in tuples
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)

    permit = validator.approved_list_for_tag_operation(tag_name)
    logger.info(f"Approved - List files for tag operation ({tag_name}) : {permit.approved}")
    if not permit.approved:
        logger.info(permit.data)
        return set()
    
    raw_output = database.get_rels_for_tag(tag_name)
    if not path_only_output:
        return raw_output
    user_output = { path for (fsid, inode, path, data, id) in raw_output }
    return user_output

def get_files_for_directory(path : str, path_only_output = True) -> list:
    """Gets and returns list of files in database which are located in given directory

    Calls database function to list file database entries whose paths begin with provided directory prefix

    Parameters
    ----------
    path : str
        Absolute path to directory
    path_only_output : bool, optional
        If True, returns file data in shortened format. Default is True
    Returns
    -------
    list[str] | list[tuple]
        Set of filepaths or set of file data in tuples
    """

    database = db.Database(utils.get_working_db())
    
    raw_output = database.get_files_by_path_prefix(path)
    if raw_output is None:
        return []
    if not path_only_output:
        return raw_output
    user_output = [ path for (fsid, inode, path, id) in raw_output ]
    return user_output

def daemon_pid():
    """Calls subprocess to request the process ID of semo's watcher service.


    Returns
    -------
    int
        PID

    Raises
    ------
    SemoException
        If the watcher executable isn't running (as daemon or as process)
    """

    try:
        return int(subprocess.check_output(["pgrep", "-f", "semo.semo_watcher"], text=True).strip())
    except Exception:
        raise SemoException("Watch daemon not running.")

def watch_directory(path : str) -> str:
    """Adds given directory tree to watch list and informs the watcher process of the change
    
    Also marks the directory's file system status in database.

    Parameters
    ----------
    path : str
        Absolute path to directory

    Returns
    -------
    str
        Response message
    """

    if not os.path.exists(path) or not os.path.isdir(path): return "invalid directory path"
    if path in utils.get_watches(): return "directory already watched"

    utils.set_watch(path)
    fsid, inode = utils.get_fsid_and_inode(path)
    database = db.Database(utils.get_working_db())

    fs_awake = database.is_known_and_is_awake_fs(fsid)
    if fs_awake is None:
        # new filesystem
        msg = "watch set for new filesystem"
    if fs_awake is False:
        database.set_fs_active(fsid)
        msg = "watch set for returning filesystem. if contents were modifified or mountpoint changed data may be lost. Run recovery"
    else:
        msg = "watch set for directory. if contents were modified data may be lost. Run recovery"
    os.kill(daemon_pid(), signal.SIGUSR1)
    return msg

def unwatch_directory(path : str):
    """Removes given directory tree from watch list and informs the watcher process of the change

    Parameters
    ----------
    path : str
        Absolute path to directory

    Returns
    -------
    str
        Response message
    """

    if path in utils.get_watches():
        utils.sleep_watch(path)
        os.kill(daemon_pid(), signal.SIGUSR1)
        return "unwatch set for directory"
    return "directory not watched"

def recover_under_directory(path : str, 
                            guarantee_abspath : bool = False, 
                            guarantee_mountpath : bool = False, 
                            guarantee_fsid : bool = False,
                            guarantee_inodes : bool = False,
                            guarantee_xattr : bool = False) -> list:
    """Attempts to update inconsistent database data from provided confirmed data

    Option sets [-a], [-x], [-fi], [-mfi], [-mf] guarantee full recovery. For other combinations ([-m]), only partial recovery may be possible.")

    Parameters
    ----------
    path : str
        Absolute path to directory
    guarantee_abspath : bool, optional
        If set, indicates that absolute paths of files in directory tree have not changed and can be trusted. Default is False
    guarantee_mountpath : bool, optional 
        If set, indicates that provided path is the mountpoint of its filesystem and paths relative to it have not changed and can be trusted. Default is False
    guarantee_fsid : bool, optional
        If set, indicates that the filesystem ID of directory tree has not changed (directory hasn't moved between filesystems) and can be trusted. Default is False
    guarantee_inodes : bool, optional 
        If set, indicates that the filesystem of directory tree supports persistent inodes and therefore they have not changed and can be trusted. Default is False
    guarantee_xattr : bool, optional 
        If set, indicates that semo data for directory was previously exported into the files' extended attributes, the extended attributes can be trusted and imported from. Default is False

    Returns
    -------
    list
        List of filepaths for which semo entries were recovered, and if applicable, list of filepaths that couldn't be recovered
    
    Raises
    ------
    SemoException
        If provided path is not a directory
    """

    path = os.path.abspath(path)
    if not os.path.isdir(path):
        raise SemoException(f"Path {path} is not a directory")

    if guarantee_xattr:
        return import_data_from_xattr(path)

    if guarantee_abspath:
        return data_repair.recover_fsid_inode_from_abspath(path)
    if guarantee_fsid and guarantee_inodes:
        return data_repair.recover_path_by_inode(path)
    if guarantee_mountpath:
        if guarantee_fsid:
            if guarantee_inodes:
                return data_repair.recover_path_by_inode(path)
            return data_repair.recover_path_inode_by_mountpath(path)
        else:
            return data_repair.partial_recover_path_inode_by_mountpath(path)
    
    return []

def clean_records():
    """Goes through database and verifies each entry is still accurate. Deletes outdated entries."""

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    entries = database.get_files_with_paths()
    for fsid, inode, filepath, entry_id in entries:
        try:
            if not validator.entry_consistent(fsid, inode, filepath):
                database.delete_file(fsid, inode)
        except SemoException:
            database.delete_file(fsid, inode, entry_id)
        if database._direct_rels_for_file(fsid, inode) == {}:
            database.delete_file(fsid, inode)

def export_data_to_xattr(dirpath : str, delete_local = False):
    """Exports semo entries for files in provided directory into the files' extended attributes.

    Parameters
    ----------
    dirpath : str
        Absolute path to directory
    delete_local : bool, optional
        If True, after entries are exported they are removed from semo database. Default is False
    """

    database = db.Database(utils.get_working_db())
    validator = v.Validator(database)
    entries = database.get_files_by_path_prefix(dirpath)
    if entries is None:
        return
    for fsid, inode, filepath, entry_id in entries:
        semo_data = database._direct_rels_for_file(fsid, inode)
        data_string = " ".join(f"{k}:{v}" for k, v in semo_data.items())
        os.setxattr(filepath, "user.semo", data_string.encode())
        if delete_local:
            database.delete_file(fsid, inode)

def import_data_from_xattr(dirpath : str):
    """Imports semo entries for files in provided directory from the files' extended attributes.

    Parameters
    ----------
    dirpath : str
        Absolute path to directory

    Returns
    -------
    list[str]
        List of paths for which entries were successfully imported
    """

    imported = []
    for contents in os.walk(dirpath):
        prefix, dirs, files = contents
        for item in dirs + files:
            filepath = os.path.join(prefix, item)
            data_string = os.getxattr(filepath, "user.semo").decode()
            if data_string:
                semo_data = dict(item.split(":") for item in data_string.split())
                for k, v in semo_data.items():
                    connect_tag(filepath, k, v)
                imported.append(filepath)
                os.setxattr(filepath, "user.semo", b"")
    return imported
