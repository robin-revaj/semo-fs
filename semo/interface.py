#!/usr/bin/env python3

from . import backend, errors as e, settings
import re

def interface_translate_TAG(args):
    file_name : str = args.filename
    tag_name : str = args.tagname

    if not backend.command_TAG(file_name, tag_name):
        print("Failed due to reasons")
        raise SystemExit(1)
    
    print("File {0} now tagged with: {1}".format(file_name, tag_name))
    raise SystemExit(0)

def interface_translate_UNTAG(args):
    file_name : str = args.filename
    tag_name : str = args.tagname

    if not backend.command_UNTAG(file_name, tag_name):
        print("Failed due to reasons")
        raise SystemExit(1)

    print("File {0} no longer tagged with {1}".format(file_name, tag_name))
    raise SystemExit(0)

def interface_translate_LISTTAGS(args):
    file_name : str = args.filename
    if file_name:
        output = backend.query_LIST_TAGS_FOR_FILE(file_name) 
        print("File {0} tagged with: {1}".format(file_name, output))
        raise SystemExit(0)
    
    output1 = backend.query_LIST_EXISTING_TAGS()
    print("All existing tags: {0}".format(output1))
    output2 = backend.query_LIST_HIERARCHY()
    for line in construct_hierarchy_tree(output2):
        print(line)


    raise SystemExit(0)

def construct_hierarchy_tree(hierarchy):
    lines = []

    def read_level(dictionairy, offset):
        if not dictionairy:
            return
        for item in dictionairy:
            prefix = "|"
            if offset == 0: prefix = ""
            lines.append((prefix + "————") * offset + item)
            read_level(dictionairy[item], offset + 1)

    read_level(hierarchy, [0])
    return lines

def interface_translate_DELTAG(args):
    tag_name : str = args.tagname
    if not backend.command_DEL_TAG(tag_name):
        print("Failed to delete tag due to reasons")
        raise SystemExit(1)
    raise SystemExit(0)

def interface_translate_SUBTAG(args):
    superior_tag : str = args.superior_tag
    unassign_flag : bool = args.unassign
    inferior_tags : list[str] = args.inferior_tag
    if inferior_tags:
        if unassign_flag:
            backend.command_UNASSIGN_SUBTAG(superior_tag, inferior_tags)
            print(f"")
        else:
            backend.command_ASSIGN_SUBTAG(superior_tag, inferior_tags)
    raise SystemExit(0)
    

def user_confirmation(message : str) -> bool:
    pattern = re.compile("[Yy]+[Ee]?[Ss]?")
    response : str = input(message + " (Y/n) ")
    return re.fullmatch(pattern, response) is not None # TODO allow more response options

def interface_command_SELECTDB(args):
    database_path : str = args.database_path
    if not database_path:
        print(settings.database_path)
        raise SystemExit(0)
    settings.database_path = database_path
    print(f"Database switched to: {database_path}")
    raise SystemExit(0)