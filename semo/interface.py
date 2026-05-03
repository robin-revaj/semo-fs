#! /usr/bin/env python3

"""
Module used to process user input, parsing it to the corresponding function and constructing responses.

Functions
---------
translate_TAG(args, suppress=False)
    Handles 'tag' instruction.
translate_UNTAG(args, suppress=False)
    Handles 'utag' instruction.
translate_LISTTAGS(args, suppress=False)
    Handles 'ls_tags' instruction.
translate_LISTROOTS(suppress=False)
    Handles 'ls_roots' instruction.
translate_LISTFILES(args, suppress=False)
    Handles 'ls_files' instruction.
translate_DELTAG(args, suppress=False)
    Handles 'deltag' instruction.
translate_SUBTAG(args, suppress=False)
    Handles 'subtag' instruction.
translate_UNSUBTAG(args, suppress=False)
    Handles 'usubtag' instruction.
translate_LISTSUBTAGS(args, suppress=False)
    Handles 'ls_subtags' instruction.
make_tree_string_for_dict(d, indent=4)
    Returns a string formatted dictionary.
translate_WATCH(args, suppress=False)
    Handles 'watch' instruction.
translate_UNWATCH(args, suppress=False)
    Handles 'uwatch' instruction.
translate_LISTWATCHES(suppress=False)
    Handles 'ls_subtags' instruction.
translate_SELECTDB(args, suppress=False)
    Handles 'db' instruction.
translate_IMPORT(args, suppress=False)
    Handles 'import' instruction.
translate_EXPORT(args)
    Handles 'export' instruction.
translate_CLEAN(args)
    Handles 'ls_subtags' instruction.
translate_MOUNT(args, suppress=False)
    Handles 'mount' instruction.
translate_UMOUNT(args, suppress=False)
    Handles 'umount' instruction.
"""

import os
import backend, utils
from utils import SemoException

def translate_TAG(args, suppress=False):
    """Reconstructs parameters filename, tagname, value from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.filename : str
        args.tagname : str
        args.value : str | int | None
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    file_name : str = os.path.realpath(args.filename)
    tag_name : str = args.tagname
    value : str | int | None = args.value
    if utils.is_integer_string(value):
        value = int(value) # type: ignore
    response = backend.connect_tag(file_name, tag_name, value)
    if response == []:
        return
    
    if not suppress: print("Failed tag due to reasons: ", response)
    return response

def translate_UNTAG(args, suppress=False):
    """Reconstructs parameters filename, tagname from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.filename : str
        args.tagname : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    file_name : str = os.path.realpath(args.filename)
    tag_name : str = args.tagname

    response = backend.disconnect_tag(file_name, tag_name)
    if response == []:
        return
    
    if not suppress: print("Failed untag due to reasons: ", response)
    return response

def translate_LISTTAGS(args, suppress=False):
    """Reconstructs parameter filename from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.filename : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    if args.filename:
        file_name : str = os.path.realpath(args.filename)
        output = backend.get_tags_for_file(file_name) 
        if not suppress: print("\n".join("{k}:{v}".format(k=k, v=v) for k, v in output.items()))
        return output
    output1 = backend.get_all_tags()
    if not suppress: print("\n".join(output1))
    return output1

def translate_LISTROOTS(suppress=False):
    """Calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    output = backend.get_roots()
    if not suppress: print(output)
    return output

def translate_LISTFILES(args, suppress=False):
    """Reconstructs parameter query from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.query : list[str] | str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    if isinstance(args.query, list):
        query : str = " ".join(args.query)
    else:
        query : str = args.query
    #shortened_format : bool = not args.long
    try:
        output = backend.query_files(query)
    except SemoException as e:
        if not suppress:
            print("Failed query with error: " + str(e))
        return str(e)
    if not suppress:
        print("\n".join("{0}    {1}".format(i, j) for i, j in output))
    return output

def translate_DELTAG(args, suppress=False):
    """Reconstructs parameter tagname from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.tagname : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    tag_name : str = args.tagname
    response = backend.delete_tag(tag_name)
    if response == []:
        return
    if not suppress: print("Failed delete tag due to reasons: ", response)
    return response

def translate_SUBTAG(args, suppress=False):
    """Reconstructs parameters superior_tag, inferior_tags from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.superior_tag : str
        args.inferior_tag : list[str]
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    superior_tag : str = args.superior_tag
    inferior_tags : list[str] = args.inferior_tag
    response = backend.connect_subtags(superior_tag, inferior_tags)
    if response == []:
        return
    if not suppress: print("Failed assign subtag due to reasons: ", response)
    return response

def translate_UNSUBTAG(args, suppress=False):
    """Reconstructs parameters superior_tag, inferior_tag from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.superior_tag : str
        args.inferior_tag : list[str]
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """

    superior_tag : str = args.superior_tag
    inferior_tags : list[str] = args.inferior_tag
    response = backend.disconnect_subtags(superior_tag, inferior_tags)
    if response == []:
        return
    if not suppress: print("Failed unassign subtag due to reasons: ", response)
    return
    
def translate_LISTSUBTAGS(args, suppress=False):
    """Reconstructs parameters tagname, direct from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.tagname : str
        args.direct : bool
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    root_tag : str = args.tagname
    direct : bool = args.direct
    if direct:
        output = backend.get_subtags_DIRECT(root_tag)
    else:
        output = make_tree_string_for_dict(backend.get_subtags(root_tag))
    if not suppress: print(output)
    return output

def make_tree_string_for_dict(d : dict, indent = 4):
    output = ""
    for k, v in d.items():
        output += " " * indent + str(k) + "\n"
        if isinstance(v, dict):
            output += make_tree_string_for_dict(v, indent + 4)
    return output

def translate_WATCH(args, suppress=False):
    """Reconstructs parameter path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    path : str = os.path.realpath(args.path)
    full_path = os.path.abspath(path)
    response = backend.watch_directory(full_path)
    if not suppress: print(response)
    return response

def translate_UNWATCH(args, suppress=False):
    """Reconstructs parameter path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    path : str = os.path.realpath(args.path)
    full_path = os.path.abspath(path)
    response = backend.unwatch_directory(full_path)
    if not suppress: print(response)
    return response

def translate_LISTWATCHES(suppress=False):
    """Calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    output = utils.get_watches()
    if not suppress: print(output)
    return output

def translate_SELECTDB(args, suppress=False):
    """Reconstructs parameter database_path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.database_path : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    database_path : str = os.path.realpath(args.database_path)
    if not database_path:
        if not suppress: print(utils.get_working_db())
        return utils.get_working_db()
    utils.set_working_db(database_path)
    if not suppress: print(f"Database switched to: {database_path}")
    return

def translate_IMPORT(args, suppress=False):
    """Reconstructs parameters path and options from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
        args.guarantee_abspath : bool
        args.guarantee_mountpath : bool
        args.guarantee_fsid : bool
        args.guarantee_inodes : bool
        args.guarantee_xattr : bool
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    path : str = os.path.realpath(args.path)
    guarantee_abspath : bool = args.guarantee_abspath
    guarantee_mountpath : bool = args.guarantee_mountpath
    guarantee_fsid : bool = args.guarantee_fsid
    guarantee_inodes : bool = args.guarantee_inodes
    guarantee_xattr : bool = args.guarantee_xattr

    output = backend.recover_under_directory(path, 
                                             guarantee_abspath, 
                                             guarantee_mountpath, 
                                             guarantee_fsid, 
                                             guarantee_inodes, 
                                             guarantee_xattr)
    if not suppress: print(output)
    return output

def translate_EXPORT(args):
    """Reconstructs parameter path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
    """
    
    path : str = os.path.realpath(args.path)
    backend.export_data_to_xattr(path)

def translate_CLEAN():
    """Calls corresponding backend function."""
    
    backend.clean_records()

def translate_MOUNT(args, suppress=False):
    """Reconstructs parameter path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    
    pass

def translate_UMOUNT(args, suppress=False):
    """Reconstructs parameter path from args, calls corresponding backend fuction, returns response.
    
    Parameters:
    -----------
    args : argparse.Namespace
        Argument set containing values for parameters
        args.path : str
    suppress : bool, optional
        If true, responses aren't printed to stdout but returned (default is False)
    """
    pass


