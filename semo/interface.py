#!.venv/bin/python3

import os

from . import backend, settings

def interface_translate_TAG(args, suppress=False):
    file_name : str = os.getcwd() + "/" + args.filename
    tag_name : str = args.tagname
    value : str | int | None = args.value
    response = backend.connect_tag(file_name, tag_name, value)
    if response == []:
        return
    
    if not suppress: print("Failed tag due to reasons: ", response)
    return

def interface_translate_UNTAG(args, suppress=False):
    file_name : str = os.getcwd() + "/" + args.filename
    tag_name : str = args.tagname

    response = backend.disconnect_tag(file_name, tag_name)
    if response == []:
        return
    
    if not suppress: print("Failed untag due to reasons: ", response)
    return

def interface_translate_LISTTAGS(args, suppress=False):
    if args.filename:
        file_name : str = os.getcwd() + "/" + args.filename
        output = backend.get_tags_for_file(file_name) 
        if not suppress: print("File {0} tagged with: {1}".format(file_name, output))
        return output
    output1 = backend.get_all_tags()
    if not suppress: print("All existing tags: {0}".format(output1))
    return output1

def translate_LISTROOTS(args, suppress=False):
    output = backend.get_roots()
    if not suppress: print(output)
    return output

def interface_translate_LISTFILES(args, suppress=False):
    try:
        query : str = args.query
    except Exception as e:
        query : str = args.query.join(" ")
        
    if hasattr(args, "long"):
        long_format : bool = args.long
    else:
        long_format = False
    output = backend.query_files(query, long_format)
    if not suppress:
        if query:
            print("Files corresponding: {0}".format(output))
        else:
            print("All files: {0}".format(output))
    return output

def interface_translate_DELTAG(args, suppress=False):
    tag_name : str = args.tagname
    response = backend.delete_tag(tag_name)
    if response == []:
        return
    if not suppress: print("Failed delete tag due to reasons: ", response)
    return

def interface_translate_SUBTAG(args, suppress=False):
    superior_tag : str = args.superior_tag
    unassign_flag : bool = args.unassign
    inferior_tags : list[str] = args.inferior_tag
    if inferior_tags:
        if unassign_flag:
            response = backend.disconnect_subtags(superior_tag, inferior_tags)
            if response == []:
                return
            if not suppress: print("Failed unassign subtag due to reasons: ", response)
            return
        response = backend.connect_subtags(superior_tag, inferior_tags)
        if response == []:
            return
        if not suppress: print("Failed assign subtag due to reasons: ", response)
    return
    
def interface_translate_LISTSUBTAGS(args, suppress=False):
    root_tag : str = args.tagname
    direct : bool = args.direct
    if direct:
        output = backend.get_subtags_DIRECT(root_tag)
    else:
        output = "placeholder"
    if not suppress: print(output)
    return output

# def interface_translate_WATCH(args):
#     path : str = args.path
#     full_path = os.getcwd() + "/" + path
#     response = backend.command_WATCH(path)
#     if response == []:
#         return
#     print("Failed to watch due to reasons: ", response)
#     return

def interface_command_SELECTDB(args, suppress=False):
    database_path : str = args.database_path
    if not database_path:
        print(settings.database_path)
        raise SystemExit(0)
    settings.database_path = database_path
    if not suppress: print(f"Database switched to: {database_path}")
    raise SystemExit(0)