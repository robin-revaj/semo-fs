#!.venv/bin/python3

import os

from . import backend, errors as e, settings
import re

def interface_translate_TAG(args):
    file_name : str = os.getcwd() + "/" + args.filename
    tag_name : str = args.tagname

    response = backend.command_TAG(file_name, tag_name)
    if response == []:
        return
    
    print("Failed tag due to reasons: ", response)
    return

def interface_translate_UNTAG(args):
    file_name : str = os.getcwd() + "/" + args.filename
    tag_name : str = args.tagname

    response = backend.command_UNTAG(file_name, tag_name)
    if response == []:
        return
    
    print("Failed untag due to reasons: ", response)
    return

def interface_translate_LISTTAGS(args):
    if args.filename:
        file_name : str = os.getcwd() + "/" + args.filename
        output = backend.query_LIST_TAGS_FOR_FILE(file_name) 
        print("File {0} tagged with: {1}".format(file_name, output))
        return output
    output1 = backend.query_LIST_ALL_TAGS()
    print("All existing tags: {0}".format(output1))
    return output1

def interface_translate_LISTFILES(args):
    query : str = args.query
    if hasattr(args, "long"):
        long_format : bool = args.long
    else:
        long_format = False
    output = backend.query_LIST_FILES(query, long_format)
    if query:
        print("Files corresponding: {0}".format(output))
    else:
        print("All files: {0}".format(output))
    return output

def interface_translate_DELTAG(args):
    tag_name : str = args.tagname
    response = backend.command_DEL_TAG(tag_name)
    if response == []:
        return
    print("Failed delete tag due to reasons: ", response)
    return

def interface_translate_SUBTAG(args):
    superior_tag : str = args.superior_tag
    unassign_flag : bool = args.unassign
    inferior_tags : list[str] = args.inferior_tag
    if inferior_tags:
        if unassign_flag:
            response = backend.command_UNASSIGN_SUBTAGS(superior_tag, inferior_tags)
            if response == []:
                return
            print("Failed unassign subtag due to reasons: ", response)
            return
        response = backend.command_ASSIGN_SUBTAGS(superior_tag, inferior_tags)
        if response == []:
            return
        print("Failed assign subtag due to reasons: ", response)
    return
    
def interface_translate_LISTSUBTAGS(args):
    root_tag : str = args.root_tag
    output = backend.query_LIST_ALL_SUBTAGS(root_tag)
    print("Subtags for root '{0}': {1}".format(root_tag, output))
    return output

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